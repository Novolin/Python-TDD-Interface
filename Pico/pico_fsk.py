# testing fsk decoding on the pico

import board
from analogio import AnalogIn
import analogbufio
import array

buffered_input = array.array("H")
analog_input = board.A0
read_led = board.GP17
'''
plan:
sample some input (10ms? at 8khz? that's 80 samples?)
count # of zero crossings
then decode bit

we want it to take < 10 ms to process, and we need a timer to ensure we get the bits/bit ends correct

'''




class TTYReader:
    def __init__(self, pin, baudrate):
        self.baudrate = baudrate
        self.pin = pin
        self.in_buff = array.array("H")