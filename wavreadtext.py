## THIS IS A TEST TO TRY SOME WAV READING ##
## IF I CAN FIGURE OUT THIS, I CAN DO FSK ##

import wave
import numpy as np 


class AudioReader:
    def __init__(self, file_name):
        self.audfile = wave.open(file_name, "rb")

    def skip_to_next_audio(self):
        # Moves the cursor to the next frame with any audio data, returns the frame it starts.
        while self.audfile.readframes(1) == b"\0\0":
            pass
        return self.audfile.tell() 

