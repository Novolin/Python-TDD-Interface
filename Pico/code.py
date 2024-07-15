# V0.02 - fsk might be working? so let's try!!!
# Still waiting on the hardware to do encoding, since I need a 4-pole headphone jack

import time
from array import array
import board
from digitalio import DigitalInOut, Direction, Pull
import pico_fsk 
import baudot_tty



recievePin = board.A3

reader = pico_fsk.TTYReader2(recievePin, 50)

reader.calibrate()
reader.init_monitor()

while True:
    while reader.await_bit:
        if reader.check_for_input():
            reader.await_bit = False
    #bit found, let's decode:

