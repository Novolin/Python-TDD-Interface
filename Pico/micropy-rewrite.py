# Trying to do stuff in micropython because it's a bit faster and I know it better now

from machine import PWM, Pin, ADC #type: ignore 
import time



class AudioCoupler:
    def __init__(self, out_pin, in_pin):
        self.audio_out = PWM(out_pin, freq = 16000) # we're just doing tones, 16k is probably overkill lmao
        self.audio_in = ADC(in_pin)
        self.block_input = False # should we be emitting tones to stop more coming in?
        self.noise_gate = 1024 # a margin to detect things are changing???
        self.zero_point = 0
        self.calibrate_audio_in()

    def get_samples(self):
        # sample an analog pin over 10ms
        sample_list = []
        sample_end = time.ticks_us() + 10000
        while time.ticks_diff(sample_end, time.ticks_us()) > 0:
            sample_list.append(self.audio_in.read_u16())
        return sample_list

    def calibrate_audio_in(self):
        # Gets a baseline for background noise/etc. 
        bg_samples = self.get_samples()
        # set a noise threshold?
        self.zero_point = sum(bg_samples)/len(bg_samples)
        self.noise_gate = self.zero_point + 1024 # idk what the correct number is


    def read_incoming_tone(self): # Very rudimentary tone analysis stuff.
        tone_samples = self.get_samples()
        # let's assume the zero point is reasonably calibrated?
        look_for_positive = True
        zero_crossings = 0
        for i in tone_samples:
            if look_for_positive:
                if i > self.zero_point:
                    zero_crossings += 1
                    look_for_positive = False
            else:
                if i < self.zero_point:
                    zero_crossings += 1
                    look_for_positive = True

