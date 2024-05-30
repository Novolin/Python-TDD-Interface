# V0.01 - Hopefully a working basic interface.

import time
import board
import baudot_tty as bd
from analogio import AnalogIn
from supervisor import ticks_ms


class Reciever:
    def __init__(self, pin):
        self.pin = pin
        self.active = False
        
