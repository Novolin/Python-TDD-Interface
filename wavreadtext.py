## THIS IS A TEST TO TRY SOME WAV READING ##

import wave
import numpy as np 


class AudioReader:
    def __init__(self, file_name):
        self.audfile = wave.open(file_name, "rb")

    def skip_to_next_audio(self)



filename = "wav/output/ryryry.wav"




with wave.open(filename, "rb") as audiotest:
    while audfile.readframes(1) == b"\0\0": # skim until 
        pass
