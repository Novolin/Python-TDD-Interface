from machine import Pin, PWM, ADC # type: ignore
from collections import deque
from micropython import const

# Character encodings
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
_LTRS_BYTE = const(0x1B)
_FIGS_BYTE = const(0x1F)


class BDInterface:
    ''' TODO: a structure for how an output object will handle interfacing with the line
        If you want to roll your own non-i2s system, you can use a subclass of this'''
    def __init__(self, baudrate = 50, mark_freq = 1400, space_freq = 1800):
        self.busy = False # idk how async stuff works but i think this might help???
        self.baudrate = baudrate
        self.bit_time = int(1000/baudrate) # bit time in ms
        self.mark_freq = mark_freq # binary 1
        self.space_freq = space_freq # binary 0

    
    def mark(self, time):
        pass # This function will play the mark freq for time ms

    def space(self, time):
        pass # this function will play the space tone for time ms

    def write_byte(self, byte):
        pass # write a single byte to the output device


class BDEncoder:
    def __init__(self, output_interface:BDInterface, baudrate:int = 50):
        '''An object that will encode data and send it over the given interface.'''
        self.baudrate = baudrate
        self.interface = output_interface 
        self.encoding_mode = LTRS
        self.encode_asserted = 99 # How many characters since we last asserted our mode.
        self.assert_at = 30 # how often we should reassert our mode in case it desyncs.
        self.output_buffer = deque((), 256) # 256 characters worth of data in our buffer. I doubt we'll need more.
        
    def sanitize_string(self, input_string:str, replace_with:str = " ", newline:str = "\n\r") -> str:
        ''' Returns a baudot-save string, with invalid characters replaced with whatever replace_with is.
            also sets carriage returns to be both return and linefeed, so you can write text more "naturally"'''
        output_string = ""
        for c in input_string.upper():
            if c == "\n":
                output_string += newline
            elif c in LTRS or c in FIGS:
                output_string += c
            else:
                output_string += replace_with
        
        return output_string
    
    def buffer_string(self, string:str):
        ''' Converts a string to numerical form, and puts it into the buffer.'''
        for c in string:
            if c not in self.encoding_mode or self.encode_asserted > self.assert_at:
                if c in LTRS:
                    self.encoding_mode = LTRS
                    self.output_buffer.append(_LTRS_BYTE)
                    self.encode_asserted = 0
                elif c in FIGS:
                    self.encoding_mode = FIGS
                    self.output_buffer.append(_FIGS_BYTE)
                    self.encode_asserted = 0
                else: # should only happen if you use an unsanitized string.
                    print("Invalid Character: " + c)
                    self.output_buffer.append(" ")
                    continue
            self.output_buffer.append(self.encoding_mode.index(c))
            self.encode_asserted += 1
        return 
    

    def send_output_buffer(self):
        ''' Outputs the contents of the buffer to the interface'''
        while len(self.output_buffer) > 0:
            self.interface.write_byte(self.output_buffer.popleft())
    
    def write(self, string:str)-> bool:
        # Sanitizes and sends a string via the buffer
        sani_string = self.sanitize_string(string) # make sure the string is sanitized
        self.buffer_string(sani_string)
        if not self.interface.busy: # in case we do dumb async stuff
            self.send_output_buffer()
        else: 
            return False # failed to send, interface busy
        return True # Sent successfully (from here at least)
