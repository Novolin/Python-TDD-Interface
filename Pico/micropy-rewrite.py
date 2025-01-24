# Trying to do stuff in micropython because it's a bit faster and I know it better now

#from machine import PWM, Pin, ADC #type: ignore 
import time
import asyncio
from collections import deque
from math import sin, pi

# Character encodings
LTRS = (
    "\b",
    "E",
    "\n",
    "A",
    " ",
    "S",
    "I",
    "U",
    "\r",
    "D",
    "R",
    "J",
    "N",
    "F",
    "C",
    "K",
    "T",
    "Z",
    "L",
    "W",
    "H",
    "Y",
    "P",
    "Q",
    "O",
    "B",
    "G",
    "FIGS",
    "M",
    "X",
    "V",
    "LTRS",
)
FIGS = (
    "\b",
    "3",
    "\n",
    "-",
    " ",
    "-",
    "8",
    "7",
    "\r",
    "$",
    "4",
    "'",
    ",",
    "!",
    ":",
    "(",
    "5",
    '"',
    ")",
    "2",
    "=",
    "6",
    "0",
    "1",
    "9",
    "?",
    "+",
    "FIGS",
    ".",
    "/",
    ";",
    "LTRS",
)

# Write some sine tables for our tones:
'''
spitballin:
these tables will be duty cycle values for our waveforms, so we should make them 
65535      1
(65535/2)  0
0         -1



'''
# constants for sine wave generation, copied from John Park's stuff for circuitpython

SIN_LENGTH = 100  # more is less choppy
SIN_AMPLITUDE = 2 ** 15  # 0 (min) to 32768 (max)  made 2^15 to allow for maximum volume. 3.5v won't do a lot on this speaker.
SIN_OFFSET = 32767.5  # for 16bit range, (2**16 - 1) / 2
DELTA_PI = 2 * pi / SIN_LENGTH  # happy little constant

sine_wave = [
    int(SIN_OFFSET + SIN_AMPLITUDE * sin(DELTA_PI * i)) for i in range(SIN_LENGTH)
]

print(sine_wave) # TODO: MAKE A THING TO TRACK ALONG THE WAVE AS WE DO AUDIOS

class AudioCoupler:
    def __init__(self, out_pin, in_pin):
        self.sample_buffer = deque([0] * 100)
        self.audio_out = PWM(out_pin, freq = 16000) # we're just doing tones, 16k is probably overkill lmao
        self.audio_in = ADC(in_pin)
        self.block_input = False # should we be emitting tones to stop more coming in?
        self.noise_gate = 1024 # a margin to detect things are changing???
        self.zero_point = 0
        self.last_sample_time = time.ticks_us()
 
    async def read_buffer_sample(self):
        # add the buffer sample to our deck, pop out whatever else was in it.
        if time.ticks_diff(self.last_sample_time, time.ticks_us()) >=100: # if it's been at least 100 uS since our last sample
            self.sample_buffer.popleft() # drop our old one
            self.sample_buffer.append(self.audio_in.read_u16()) # read a new one
            return True
        return False # we have to wait for the next time to do it.
        

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

        if zero_crossings > 32: # in 10ms it should be 36 for 1800 and 28 for 14
            return 0 # return our detected bit level
        else:
            return 1

    def read_data_byte(self, start_time):
        byte = 0

    async def run_audio_interface(self):
        while True:
            while not self.block_input:
                # poll for incoming data:
                if not self.read_incoming_tone():
                    #start bit! do a read loop.
                    read_data_byte(start_time)

