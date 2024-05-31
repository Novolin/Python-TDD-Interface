# testing fsk decoding on the pico

import board
from analogio import AnalogIn
import analogbufio
import array


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
        self.in_buff = array.array("H", [0]*80) # 80 samples = 10 ms
        self.analog_reader = False

    def init_reader(self):
        try:
            self.analog_reader = analogbufio.BufferedIn(self.pin, sample_rate = 8000) # 8khz samples should be ok?
            return True
        except:
            return False

    def read_data(self):
        if self.analog_reader == False:
            print("Error: Initialize reader first!!")
            return False
        self.analog_reader.readinto(self.in_buff)
        return self.in_buff

    def deinit_reader(self):
        if self.analog_reader:
            self.analog_reader.deinit()
        self.analog_reader = False
        return

    def get_sampled_freqency(self):
        # count zero crossings.
        pass