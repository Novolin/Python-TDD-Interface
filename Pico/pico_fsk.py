# testing fsk decoding on the pico

import board
import analogbufio
import array

buffered_input = array.array("H")

'''
plan:
sample some input (10ms? at 8khz? that's 80 samples?)

'''


class TTYReader:
    def __init__(self, pin, baudrate):
        self.baudrate = baudrate
        self.pin = pin
        self.in_buff = array.array("H")