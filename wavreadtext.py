## THIS IS A TEST TO TRY SOME WAV READING ##
## IF I CAN FIGURE OUT THIS, I CAN DO FSK ##

import aubio
import numpy as np 

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

class AudioReader:
    def __init__(self, file_name, baudrate):
        self.bit_size = int(44100/baudrate)
        self.src = aubio.source(file_name, hop_size = self.bit_size)
        self.pitch = aubio.pitch(hop_size = self.bit_size)
        self.byte_length = self.bit_size * 7 # 5 bit byte + start and stop bits.
        self.rawdata = []
        

    def get_data_packets(self):
        # take the audio and pull out the data packets:
        awaiting_start_bit = True
        bybuff = 0b11111
        bcount = 7
        while True: # iterate the whole file
            data, count = self.src.do()
            if awaiting_start_bit:
                if self.pitch(data) > 1700:
                    awaiting_start_bit = False
                    bybuff = 0
                    bcount = 0
            else:
                if bcount < 6: 
                    bybuff = bybuff << 1
                    bcount += 1
                    if self.pitch(data) > 1700:
                        bybuff = bybuff | 0
                    else:
                        bybuff = bybuff | 1
                    if bcount == 6:
                        self.rawdata.append(bybuff)
                        awaiting_start_bit = True
            if count < self.bit_size:
                break

    def get_as_text(self):
        if self.rawdata == []:
            return False
        out_str = ""
        ltrs = True
        for i in self.rawdata:
            if ltrs:
                if i == 0x1b:
                    ltrs = False
                elif i==0x1f:
                    ltrs = True
                else: 
                    try:
                        out_str += LTRS[i]
                    except:
                        print(i)
            else: 
                if i == 0x1b:
                    ltrs = False
                elif i==0x1f:
                    ltrs = True
                else: 
                    try:
                        out_str += FIGS[i]
                    except:
                        print(i)


        return out_str

    
filename = "wav/output/HELLO_50.wav"

test = AudioReader(filename, 50)

test.get_data_packets()


print(test.get_as_text())

    