 # TODO: EVERYTHING

# this is the gui version!

from tkinter import Tk
from tkinter import *
from tkinter import ttk
import textwrap
from pydub import AudioSegment 



bit_1_50 = AudioSegment.from_file("wav/tones/1400.wav", format = "wav")
bit_0_50 = AudioSegment.from_file("wav/tones/1800.wav", format = "wav")
bit_1_45 = AudioSegment.from_file("wav/tones/1400_22.wav", format = "wav")
bit_0_45 = AudioSegment.from_file("wav/tones/1800_22.wav", format = "wav")


audio_data = {"LTRS":{},
        "FIGS":{}
        }

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

def make_byte_audio(data):
    if baud_rate.get() == 50:
        bit_0 = bit_0_50
        bit_1 = bit_1_50
    else:
        bit_0 = bit_0_45
        bit_1 = bit_1_45
    # Takes a 5 bit int, returns a TTY compatible audio tone
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

def make_message_audio(message):
    out_wav = AudioSegment.silent(100) # Add a small silence at the start of the byte
    ltrs_used = True
    out_wav += audio_data["LTRS"]["LTRS"] 
    for letter in message:
        if letter in LTRS:
            if not ltrs_used:
                out_wav += audio_data["LTRS"]["LTRS"]
                ltrs_used = True
            out_wav += audio_data["LTRS"][letter]
        else:
            if ltrs_used:
                out_wav += audio_data["LTRS"]["FIGS"]
                ltrs_used = False
            out_wav += audio_data["FIGS"][letter]

    return out_wav

def load_audio_files():
    for i in LTRS:
        audio_data["LTRS"][i] = make_byte_audio(LTRS.index(i))
    for i in FIGS: # I know repeating this is less efficient than copying it over somehow, but this is easier to write
        audio_data["FIGS"][i] = make_byte_audio(FIGS.index(i))

def sanitize_text(in_string):
    out_string = ""
    for l in in_string:
        if l not in LTRS and l not in FIGS:
            if skip_bad.get(): # if it's not a full line just nuke it
                out_string += " "
        else:
            out_string += l
    # now we do weird line shit to make it play nice with a 25 character printer lmao
    out_string = "\n".join("\n".join(textwrap.wrap(x, 25)) for x in out_string.splitlines())

    return out_string

def clear_entries():
    # TODO add a prompt?
    entry_box.delete("1.0", "end" )


def save_file():
    load_audio_files()
    text_in = sanitize_text(entry_box.get("0.0", "end").upper())
    #TODO: check for blank or overlapping file names
    outname = "wav/output/" + filename.get() + ".wav"

    audio_to_output = make_message_audio(text_in)
    audio_to_output.export(outname, format = "wav")

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
filename = StringVar(value="encoded")
baud_rate = IntVar(value=50)
preview = StringVar(value="")

content = ttk.Frame(root, padding=(5,5,10,10))
preview_frame = ttk.LabelFrame(content, text="Preview", padding=(5,5,10,10))
options_frame = ttk.LabelFrame(content, padding=(10,10,10,10), text="Options")
baud_frame = ttk.LabelFrame(options_frame, text="Baud Rate:")

filename_box = ttk.Entry(options_frame, textvariable=filename)
filename_label = ttk.Label(options_frame, text= "File Name:")
clear_button = ttk.Button(options_frame, command=clear_entries, text="Clear")
save_button = ttk.Button(options_frame, command=save_file, text="Save", state="disabled")



baud_45 = ttk.Radiobutton(baud_frame, text="45.5", variable=baud_rate, value = 45)
baud_50 = ttk.Radiobutton(baud_frame, text="50", variable=baud_rate, value = 50)
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


## RUN IT ##
root.mainloop()