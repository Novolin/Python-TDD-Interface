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
    def __init__(self, baudrate):
        if baudrate == 50:
            self.bit_size = 882
        else:
            self.bit_size = 970
        self.src = False
        self.pitch = aubio.pitch(hop_size = self.bit_size)
        self.byte_length = self.bit_size * 7 # 5 bit byte + start and stop bits.
        self.rawdata = []
        
    def set_input_source(self, filename):
        self.src = aubio.source(filename, hop_size = self.bit_size)

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
        if not self.src: # if file isn't set
            print("Error: Select a file to read")
            return False
        if self.rawdata == []:
            self.get_data_packets()
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

