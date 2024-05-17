# shifting to an object based option since that's more managable in some ways

from tkinter import Tk
from tkinter import *
from tkinter import ttk
import textwrap
from pydub import AudioSegment 
import simpleaudio as sa


# Character encodings/list
LTRS = (
    "\b",
    "E",
    "\n",
    "A",
    " ",
    "S",
    "I",
    "U",
    "\r",
    "D",
    "R",
    "J",
    "N",
    "F",
    "C",
    "K",
    "T",
    "Z",
    "L",
    "W",
    "H",
    "Y",
    "P",
    "Q",
    "O",
    "B",
    "G",
    "FIGS",
    "M",
    "X",
    "V",
    "LTRS",
)
FIGS = (
    "\b",
    "3",
    "\n",
    "-",
    " ",
    "-",
    "8",
    "7",
    "\r",
    "$",
    "4",
    "'",
    ",",
    "!",
    ":",
    "(",
    "5",
    '"',
    ")",
    "2",
    "=",
    "6",
    "0",
    "1",
    "9",
    "?",
    "+",
    "FIGS",
    ".",
    "/",
    ";",
    "LTRS",
)

def make_byte_audio(data, rate):
    # Takes a 5 bit int, returns a TTY compatible audio tone
    if rate == 50:
        bit_0 = AudioSegment.from_file("wav/tones/1800.wav", format = "wav")
        bit_1 = AudioSegment.from_file("wav/tones/1400.wav", format = "wav")
    else:
        bit_0 = AudioSegment.from_file("wav/tones/1800_22.wav", format = "wav")
        bit_1 = AudioSegment.from_file("wav/tones/1400_22.wav", format = "wav")

    out_audio = AudioSegment.empty()
    out_audio += bit_0 # Start bit
    for i in range(5):
        if data & 0b1:
            out_audio += bit_1
        else:
            out_audio += bit_0
        data = data >> 1
    while len(out_audio)< 300:
        out_audio += bit_1
    out_audio += AudioSegment.silent(50) #50 ms anti-echo
    return out_audio

def sanitize_text(in_string):
    out_string = ""
    for l in in_string:
        if l not in LTRS and l not in FIGS:
            if skip_bad.get(): # if it's not a full line just nuke it
                out_string += " "
        else:
            out_string += l
    # now we do weird line shit to make it play nice with a 25 character printer lmao
    out_string = "\r".join("\r".join(textwrap.wrap(x, 25)) for x in out_string.splitlines())

    return out_string

class BaudotEncoder:
    # Class to encode outgoing data
    def __init__(self, baud_rate):
        self.baud_rate = baud_rate
        self.audio_data = {"LTRS":{},
            "FIGS":{}
            }
        for i in LTRS:
            self.audio_data["LTRS"][i] = make_byte_audio(LTRS.index(i), baud_rate)
        for i in FIGS:
            self.audio_data["FIGS"][i] = make_byte_audio(FIGS.index(i), baud_rate)
        self.assert_ltrs = make_byte_audio(0b11111, baud_rate)
        self.assert_figs = make_byte_audio(0b11011, baud_rate)
        self.last_assert_type = "LTRS"
        self.last_assert_at = 0
        self.audio_player = False
        self.export_progress = 0 # how many characters have been exported to file

    def make_message_audio(self, message):
        out_wav = AudioSegment.silent(150) # Add a small silence at the start of the byte
        out_wav += self.audio_data["LTRS"]["LTRS"] 
        for letter in message:
            if letter in LTRS:
                if self.last_assert_type != "LTRS" or self.last_assert_at > 9:
                    out_wav += self.assert_ltrs
                    self.last_assert_at = 0
                    self.last_assert_type = "LTRS"
                out_wav += self.audio_data["LTRS"][letter]
                self.last_assert_at += 1
            else:
                if self.last_assert_type != "FIGS" or self.last_assert_at > 9:
                    out_wav +=  self.assert_figs
                    self.last_assert_at = 0
                    self.last_assert_type = "FIGS"
                out_wav += self.audio_data["FIGS"][letter]
                self.last_assert_at += 1
        return out_wav
    
    def play_audio_data(self, message):
        msg_to_play = self.make_message_audio(message)
        self.audio_player = sa.play_buffer(msg_to_play.get_array_of_samples(), 1, 2, 44100)



class BaudotDecoder:
    # Object to decode incoming audio data
    def __init__(self, rate):
        self.baud_rate = rate

    # FSK is slowly revealing its mysteries to me, here's some plans:
        '''
        decode recorded files only for now. I don't have the setup to poll a mic right now
        
        Detect volume spike at start of each bit
        slice off each bit, 1 bit length long (150/165ms) (note: LTRS/FIGS switches will run right into the next bit. double check timing with real capture.)
        measure frequency of 20/22ms sample after spike (970 frames for 45.5)
        repeat 5x?



        if first sample is 1800: We're good. if not: bad data

        rest of samples are the raw bit data

        What library to use?

        How can I detect volume spikes?

        how do I measure frequency?
        '''


encoders = [BaudotEncoder(50), BaudotEncoder(45)]
def clear_entries(calling_window):
    entry_box.delete("1.0", "end" )
    preview_text()
    calling_window.destroy()
    

def confirm_clear(msg):
    conf_window = Toplevel(root)
    conf_window.title = msg
    do_confirm = ttk.Button(conf_window, text="Yes", command=lambda: clear_entries(conf_window))
    do_cancel = ttk.Button(conf_window, text="No", command=lambda: conf_window.destroy())
    confirm_text = ttk.Label(conf_window, text="Are you sure you want to "+msg)
    confirm_text.grid(row=0, column=0, columnspan=2)
    do_confirm.grid(row=1, column=1)
    do_cancel.grid(row=1, column=0)

def save_file():
    text_in = sanitize_text(entry_box.get("0.0", "end").upper())
    #TODO: check for blank or overlapping file names
    outname = "wav/output/" + filename.get() + ".wav"

    audio_to_output = encoders[baud_rate.get()].make_message_audio(text_in)
    audio_to_output.export(outname, format = "wav")
    show_success_dialog()


def show_success_dialog():
    cdialog = Toplevel(root)
    cdialog.title= "Export Successful!"
    out_text = "Data encoded to " + filename.get() + ".wav"
    cdial_out_txt = ttk.Label(cdialog, text=out_text)
    okbutton = ttk.Button(cdialog, text="Ok", command=cdialog.destroy)
    cdial_out_txt.grid(row=0, column=0)
    okbutton.grid(row=1, column=0)


def preview_text():
    text_preview = sanitize_text(entry_box.get(0.0,"end").upper())
    preview.set(text_preview)


def verify_input(key_input = False):
    preview_text()
    # Should we allow the user to save the file?
    allow_save = True
    if filename_box.get() == "":
        allow_save = False
    if preview.get() == "":
        allow_save = False
    if allow_save:
        save_button['state'] = NORMAL
    else:
        save_button['state'] = DISABLED


### UI ###
root = Tk()

limit_chars = BooleanVar(value = True)
skip_bad = BooleanVar(value=True)
filename = StringVar(value="")
baud_rate = IntVar(value=0)
preview = StringVar(value="")

content = ttk.Frame(root, padding=(5,5,10,10))
preview_frame = ttk.LabelFrame(content, text="Preview", padding=(5,5,10,10))
options_frame = ttk.LabelFrame(content, padding=(10,10,10,10), text="Options")
baud_frame = ttk.LabelFrame(options_frame, text="Baud Rate:")
playback_frame = ttk.LabelFrame(content, text="Direct Audio Output:")

filename_box = ttk.Entry(options_frame, textvariable=filename)
filename_label = ttk.Label(options_frame, text= "File Name:")
clear_button = ttk.Button(options_frame, command=lambda: confirm_clear("clear inputs?"), text="Clear")
save_button = ttk.Button(options_frame, command=save_file, text="Save", state="disabled")

play_button = ttk.Button(playback_frame, text="Play", command=lambda: encoders[baud_rate.get()].play_audio_data(sanitize_text(entry_box.get(0.0, "end").upper())))
stop_button = ttk.Button(playback_frame, text="Stop", command= lambda: encoders[baud_rate.get()].audio_player.stop())

baud_45 = ttk.Radiobutton(baud_frame, text="45.5", variable=baud_rate, value = 1)
baud_50 = ttk.Radiobutton(baud_frame, text="50", variable=baud_rate, value = 0)
bad_box = ttk.Checkbutton(options_frame, text="Replace Unsupported\nCharacters", variable= skip_bad, onvalue=True)

entry_box = Text(content, width=25)

preview_box = ttk.Label(preview_frame, padding=(N,S,E,W), textvariable=preview, font="Fixedsys", width=25)


content.grid(column=0, row=0)
## OPTIONS BOX ##
options_frame.grid(column=0, row=0, columnspan=2, sticky=(N,S,E,W))
baud_frame.grid(column=0, row=0)
baud_45.grid(column=0, row=0, sticky="W")
baud_50.grid(column=0,row=1, sticky="W")
filename_label.grid(column=0, row = 1)
filename_box.grid(column=1, columnspan= 2,row = 1)
filename_box.bind("<KeyRelease>", verify_input)
clear_button.grid(column=0, row=2)
save_button.grid(column=1, row=2)
bad_box.grid(column=1, row=0)

## TEXT ENTRY ##
entry_box.grid(column=0, row = 1)
entry_box.bind("<KeyRelease>",verify_input)

preview_frame.grid(column = 1, row = 1, sticky=(N,S,E,W))
preview_box.grid()

## PLAYBACK ##
play_button.grid(column=0,row=0)
stop_button.grid(column=1, row=0)
playback_frame.grid(column=0, row=2, columnspan= 2)

## RUN IT ##
root.mainloop()