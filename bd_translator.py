# String Encoder to TTY/TDD compatible audio

from pydub import AudioSegment


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

print("Loading Audio Files.", end = "")
bit_start = AudioSegment.from_file("wav/start.wav")
print(".", end="")
bit_end = AudioSegment.from_file("wav/end.wav", format = "wav")
print(".", end="")
bit_1 = AudioSegment.from_file("wav/tone_1.wav", format = "wav")
print(".", end="")
bit_0 = AudioSegment.from_file("wav/tone_0.wav", format = "wav")
print(".", end="")

# Function town!
def check_message(input_string):
    for l in input_string:
        if l not in LTRS and l not in FIGS:
            return l
    return False
            

def make_byte_audio(data):
    # Takes a 5 bit int, returns a TTY compatible audio tone
    out_audio = bit_start
    
    for i in range(5):
        if data & 0b10000:
            out_audio += bit_1
        else:
            out_audio += bit_0
        data = data << 1

    out_audio += bit_end
    return out_audio

def make_message_audio(message):
    out_wav = AudioSegment.empty()
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

# Loading:
for i in LTRS:
    audio_data["LTRS"][i] = make_byte_audio(LTRS.index(i))
    print(".",end="")
for i in FIGS: # I know repeating this is less efficient than copying it over somehow, but this is easier to write
    audio_data["FIGS"][i] = make_byte_audio(FIGS.index(i))
    print(".", end="") 

print("\n Data loaded!")

running = True
while running:
    string_to_encode = input("Enter Text To Encode or '~EXIT' to quit:\n>").upper()
    if string_to_encode == "~EXIT":
        running = False
    elif check_message(string_to_encode):
        print("Invalid string: '" + check_message(string_to_encode) + "' is not a valid character.")
    else: 
        print("Creating File for String: " + string_to_encode)
        file_output = make_message_audio(string_to_encode)
        save_to = input("Enter Filename:\n>")
        
        file_output.export("wav/output/" + save_to + ".wav", format = "wav")
        print("Saved!")
        





