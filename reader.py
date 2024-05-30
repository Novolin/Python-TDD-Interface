######################
# Baudot FSK Decoder #
#    Version 1.0     #
######################


import wave

class TDDReader:
    def __init__(self, baudrate = 50, verbose = True):
            self.baudrate = baudrate
            self.LTRS = (
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
            self.FIGS = (
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
            self.last_msg = ""
            self.file = False
            self.noise_threshold = 150 # how forgiving should we be of noise
            self.audio_rate = 44100 # default 44100
            self.bit_size = int(1000/baudrate) # default for 50 baud
            self.byte_length = int(self.bit_size * 7.5) # 7.5 bits @ 50 baud
            self.verbose = verbose
    
    def get_frequency(self, data) -> int:
        # basic counter for the number of times the 0 threshold is crossed
        zeroCount = 0
        current_sign = 1
        for point in data:
            if point * current_sign > 0:
                zeroCount += 1
                current_sign = current_sign * -1 # flip the sign
        
        # Now calculate the rate of crossings:
        if zeroCount > 64:
             return 1800 # 1800 Hz, binary 0
        else:
             return 1400 # 1400 Hz, binary 1

    def decode_byte(self, data) -> int:
        # decode a byte, return its value as an integer.
        out_val = 0b00000
        if self.verbose:
            print(".", end="")
        data_start = 0
        for i in range(6):
            out_val = out_val << 1
            if self.get_frequency(data[data_start:data_start + self.bit_size]) == 1400:
                to_add = 1
            else:
                to_add = 0
            out_val = out_val | to_add
            
            data_start += self.bit_size
        return out_val

    def get_data_start(self, data) -> int:
        count = 0
        while data[count] == 0:
            count += 1
        return count
    
    def decode_baudot_string(self, data) -> str:
        mode = self.LTRS
        out_str = ""
        for i in data:
            if i == 31:
                mode = self.LTRS
            elif i == 27: 
                mode = self.FIGS
            else:
                out_str += mode[i]
        return out_str



    def decode_file(self, filename)-> str:
        self.file = filename 
        decode_list = []
        decode_string = ""
        if self.verbose:
            print("Loading " + filename + "...")
        file_data = wave.open(filename)
        # Make sure our sample math is correct:
        self.audio_rate = file_data.getframerate()
        self.bit_size = int(self.audio_rate/self.baudrate)
        self.byte_length = int(self.bit_size * 7.5)

        # RAM is cheap on modern PCs, so we can just dump the file into memory
        rawdata = []
        
        for i in range(file_data.getnframes()):
            rawdata.append(int.from_bytes(file_data.readframes(1), "little", signed = True))
        if self.verbose:
            print("Done! " + str(file_data.getnframes()) + " samples read!\nDecoding Data...", end="")

        file_data.close() # We can let the file be happy

        ##########################
        ## NOW WE READ THE DATA ##
        ##########################

        byte_start_point = self.get_data_start(rawdata)
        byte_end_point = byte_start_point + self.byte_length
        while byte_end_point < len(rawdata):
        # Search for start bit:

            decode_list.append(self.decode_byte(rawdata[byte_start_point:byte_end_point]))
            byte_start_point = byte_end_point
            byte_end_point = byte_start_point + self.byte_length
        print(decode_list)    
        decode_string = self.decode_baudot_string(decode_list)
        return decode_string
            

        
             
             


        ## im gettin mad so its break time ##


