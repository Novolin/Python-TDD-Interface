# Rewritten decoder
# Trying some different things!

import wave
import numpy as np

class TTYRead:
    def __init__(self, baudrate) -> None:
        self.baudrate = baudrate
        self.lastmessage = ""
    
    def get_frequency(self, data:ndarray) -> int:
        # basic counter for the number of times the 0 threshold is crossed
        zeroCount = 0
        current_sign = 1
        for point in data:
            if point * current_sign > 0:
                zeroCount += 1
                current_sign = current_sign * -1 # flip the sign
        
        return zeroCount

    def decode_file(self, filename):
        pass 
        # 
