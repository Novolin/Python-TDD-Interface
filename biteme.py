# now testing some dumb shit

from machine import PWM, Pin #type: ignore
import time

class ToneMaker:
    def __init__(self, pin):
        # yells at a freq given by you, the user!!!
        # start with nothing outputting because fuck you i want silence
        self.volume = 2 # quiet because it's annoying
        self.pwm = PWM(pin, freq = 1400, duty_u16 = 0) #start on mute
        

    def play_freq(self, tone, duration = 100):
        start_time = time.ticks_us()
        self.pwm.freq(tone)
        self.pwm.duty_u16(int(65535 * (self.volume / 100)))
        while time.ticks_diff(time.ticks_us(), start_time) < duration:
            pass # lmao barf
        self.pwm.duty_u16(0) # do minimum

    def change_vol(self, vol_amt):
        # changes volume to amount %
        self.volume = int(65535 * (vol_amt / 100))