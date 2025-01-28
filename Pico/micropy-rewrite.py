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
# constants for sine wave generation, copied from John Park's stuff for circuitpython

SIN_LENGTH = 100  # more is less choppy
SIN_AMPLITUDE = 2 ** 15  # 0 (min) to 32768 (max)  made 2^15 to allow for maximum volume. 3.5v won't do a lot on this speaker.
SIN_OFFSET = 32767.5  # for 16bit range, (2**16 - 1) / 2
DELTA_PI = 2 * pi / SIN_LENGTH  # happy little constant

SINE_WAVE = [
    int(SIN_OFFSET + SIN_AMPLITUDE * sin(DELTA_PI * i)) for i in range(SIN_LENGTH)
]



class ToneOutput: # only good to ~ 8khz!!!
    def __init__(self, tone_freq, out_pin):
        self.freq = tone_freq
        self.output = PWM(out_pin, freq = 16000)  # if you need higher freq, change the freq here to adapt.
        self.playing = False
        self.step = 0 # Where in our sine table are we

    def change_tone(self, new_freq):
        self.freq = new_freq
    

    async def play_tone(self):
        # will play (very slightly slower) than self.freq until otherwise stopped.
        self.playing = True
        while self.playing:
            self.step += 1
            self.output.duty_u16(SINE_WAVE[self.step])
            
            asyncio.sleep(1/(self.freq * SIN_LENGTH)) # wait for the next point. 
        return # if we're not playing, we can end this task
            
    def stop_tone(self):
        self.playing = False
        # This should cause the while loop in play_tone() to end.

class AudioCoupler:
    def __init__(self, out_pin, in_pin):
        self.active = False
        self.sample_buffer = deque([0] * 100)
        self.audio_out = ToneOutput(1400, out_pin)
        self.audio_in = ADC(in_pin)
        self.block_input = False # should we tie up the line?
        self.noise_gate = 1024 # a margin to detect things are changing???
        self.zero_point = 0
        self.last_sample_time = time.ticks_us()
        self.last_bit_start = False
        self.outgoing_mesage_buffer = "" 
        self.incoming_message_buffer = "" 
        self.input_mode = LTRS
        
    def decode_byte(self, byte):
        charout = self.input_mode[byte]
        if charout == "LTRS":
            self.input_mode = LTRS
        elif charout == "FIGS":
            self.input_mode = FIGS
        else:
            self.incoming_message_buffer += charout 
        
 
    async def check_for_signal(self):
        # Sample the line to see if we have any kind of noise coming in
        start_sample = time.ticks_ms():
        out_of_thresh_count = 0 # how many samples are outside of our threshold
        while time.ticks_diff(start_sample, time.ticks_ms()) < 2: # just a tiny bit here
            samp = self.audio_in.read_u16()
            if samp > 32768 + self.noise_gate or samp < 32768 - self.noise_gate:
                # if we're outside of our noise gate, add to a counter.
                out_of_thresh_count +=1
            asyncio.sleep(0.0001) # 100 us per sample should be ok to detect stuff?
        if out_of_thresh_count > 5:
            return True # we get signal
        else:
            return False # no signal 
            

    def sample_into_buffer(self):
        # Reads 10ms worth of data into a buffer
        self.last_sample_time = time.ticks_ms()
        while time.ticks_diff(self.last_sample_time, time.ticks_ms()) < 10: # Keep loopin til we've done this for 10ms
            last_read = time.ticks_us()
            self.sample_buffer.popleft() # dump the old sample
            self.sample_buffer.append(self.audio_in.read_u16()) # add a new one
            while time.ticks_diff(time.ticks_us(), last_read) < 10:
                pass # wait for our next sample period. Should be ~10kHz
            
        
    def calibrate_audio_in(self):
        # Gets a baseline for background noise/etc. 
        bg_samples = self.get_samples()
        # set a noise threshold?
        self.zero_point = sum(bg_samples)/len(bg_samples)
        self.noise_gate = self.zero_point + 1024 # idk what the correct number for this is, i'll have to play around with it.


    def read_incoming_tone(self): # Very rudimentary tone analysis stuff.
        tone_samples = list(self.sample_buffer)
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

    def read_data_byte(self): # we will drop everything to run this because it is timing critical
        byte = 0
        bitcount = 0:
        while bitcount < 5:
            self.last_bit_start = time.ticks_ms() 
            self.sample_into_buffer() # should take ~10ms
            byte = byte << 1 | self.read_incoming_tone()
            bitcount += 1
            while time.ticks_diff(time.ticks_ms(), self.last_bit_start) < 20: # each bit is 20 ms long
                pass # just fuckin wait for another 10ms
        return byte
        
        


    