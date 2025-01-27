# now testing some dumb shit

from machine import PWM, Pin #type: ignore
import time

class ToneMaker:
    def __init__(self, pin):
        # yells at a freq given by you, the user!!!
        # start with nothing outputting because fuck you i want silence
        self.volume = 65535 * (1/10) # 10% volume???
        self.pwm = PWM(pin, freq = 0, duty_u16 = self.volume)
        

    def play_freq(self, tone, duration = 100):
        start_time = time.ticks_us()
        self.pwm.freq(tone)
        while time.ticks_diff(time.ticks_us(), start_time) < duration:
            pass # lmao barf
        self.pwm.freq(0)

    def change_vol(self, vol_amt):
        # changes volume to amount %
        self.volume = 65535 * (vol_amt / 100)
        self.pwm.duty_u16(self.volume)