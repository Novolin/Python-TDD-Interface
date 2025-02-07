# just cleaning up based on what i've learned
# add some better comments here, nerd!



from machine import PWM, Pin, ADC #type: ignore 
from micropython import const #type:ignore
import time
import asyncio
from collections import deque
from math import sin, pi
from micropython import const #type:ignore

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
# a table of sine wave values for pwm!
SINE_WAVE = [
    int(SIN_OFFSET + SIN_AMPLITUDE * sin(DELTA_PI * i)) for i in range(SIN_LENGTH)
]

_BAUDOT_ONE = const(1/140000) # sample period for 1400 Hz tone
_BAUDOT_ZERO = const(1/180000) # sample period for 1800 Hz


class BaudotOutput:
    def __init__(self, out_pin):
        self.output = PWM(out_pin, freq = 16000)  # if you need higher freq, change the freq here to adapt.
        self.line_val = 1 # what value is being output to the line
        self.buffered_out = deque(())
        self.out_mode = LTRS # what output mode are we in
        self.rts_trigger = asyncio.Event() # event to trigger an RTS condition.
        self.sample_position = 0 # where in the sine table are we. Used for smooth transitions between freqencies.

    def buffer_string(self, string_to_buffer:str):
        # Adds string to the output buffer, and sets the trigger for RTS.
        # Ensure we end with a newline
        if string_to_buffer[-1] != "\n":
            string_to_buffer += "\n"
        
        self.buffered_out.clear()
        char_count = 0 # a counter to know when to reassert LTRS/FIGS
              
        for c in string_to_buffer: 
            # First check if we need to assert mode:
            if char_count % 10 ==  0 or c not in self.out_mode: 
                # next check for the correct mode to set
                if c in LTRS:
                    self.buffered_out.append(0x1B)
                    self.out_mode = LTRS
                elif c in FIGS:
                    self.buffered_out.append(0x1F)
                    self.out_mode = FIGS
                elif self.out_mode == LTRS: # if it's not a valid character, just reassert what we have already.
                    self.buffered_out.append(0x1B)
                else:
                    self.buffered_out.append(0x1F)

            char_count += 1
            if c in self.out_mode:
                self.buffered_out.append(self.out_mode.index(c))
            else:
                self.buffered_out.append(4) # if it's not found, append a space, this works in FIGS or LTRS
        return char_count # return # of chars buffered.
        
    def play_tone(self, duration, value):
        # Plays the tone for a given value for the given # of ms
        # blocks further execution because timing is very sensitive on this bad boy.
        start_time = time.ticks_ms()
        while time.ticks_diff(start_time, time.ticks_ms) < duration:
            self.output.duty_u16(SINE_WAVE[self.sample_position])
            self.sample_position += 1
            time.sleep_us(value)

    async def play_data_tones(self): 
        # waits for RTS event, then plays data tones for the correct period
        await self.rts_trigger.wait()
        # RTS recieved, now we can play tones
        while len(self.buffered_out > 0):
            next_byte = self.buffered_out.popleft()
            bitcount = 0
            self.play_tone(20,_BAUDOT_ZERO) # start bit
            while bitcount < 5: # now do the whole byte
                if next_byte >> bitcount & 1: # If the bits are backwards, this is where you messed up.
                    self.play_tone(20,_BAUDOT_ONE)
                else:
                    self.play_tone(20,_BAUDOT_ZERO)
                bitcount += 1
            self.play_tone(30,_BAUDOT_ONE) # stop bit
        self.play_tone(150, _BAUDOT_ONE) # extend carrier tone to reduce echo


class BaudotInput:
    def __init__(self, adc_pin):
        self.line_in = ADC(adc_pin)
        self.read_mode = LTRS # default to reading in LTRS mode
        self.data_buffer = deque(()) # buffer for incoming data
        self.input_lock = asyncio.Lock()