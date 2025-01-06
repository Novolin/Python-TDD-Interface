# Trying to do stuff in micropython because it's a bit faster and I know it better now

from machine import PWM, Pin, ADC #type: ignore 
import time



class AudioCoupler:
    def __init__(self, out_pin, in_pin):
        self.audio_out = PWM(out_pin, freq = 16000) # we're just doing tones, 16k is probably overkill lmao
        self.audio_in = ADC(in_pin)

    def get_samples(self):
        sample_start = time.time_us()
        # returns a list of samples taken over 5 ms? 10?
        pass

