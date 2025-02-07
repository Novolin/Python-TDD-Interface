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


# sync events for rx/tx
send_trigger = asyncio.Event()
receive_trigger = asyncio.Event() 


class BaudotOutput:
    def __init__(self, out_pin, send_trigger = send_trigger):
        self.output = PWM(out_pin, freq = 16000)  # if you need higher freq, change the freq here to adapt.
        self.line_val = 1 # what value is being output to the line
        self.buffered_out = deque(())
        self.out_mode = LTRS # what output mode are we in
        self.rts_trigger = send_trigger # event to trigger an RTS condition.
        self.sample_position = 0 # where in the sine table are we. Used for smooth transitions between freqencies.

    def buffer_string(self, string_to_buffer:str):
        # Adds string to the output buffer, and sets the trigger for RTS.
        # Ensure we end with a newline
        if string_to_buffer[-1] != "\n":
            string_to_buffer += "\n"
    
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

    async def play_data_tones(self, lock:asyncio.Lock): 
        # waits for i/o unlock, then plays data tones for the correct period
        async with lock:
            while len(self.buffered_out) > 0:
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
            self.play_tone(150, _BAUDOT_ONE) # extend carrier tone to reduce echo/mess


class BaudotInput:
    def __init__(self, adc_pin, io_lock):
        self.line_in = ADC(adc_pin)
        self.read_mode = LTRS # default to reading in LTRS mode
        self.data_buffer = deque(()) # buffer for incoming data
        self.noise_floor = 1024 # how much noise on the line before we detect signal
        self.active = False # are we currently listening to a tone
        self.io_lock = io_lock

    async def listener(self):
         # When we have the all clear to listen
        sample = self.line_in.read_u16()
        if sample > 32768 + self.noise_floor or sample < 32768 - self.noise_floor:
            bit_start = time.ticks_ms() # flag when it happened
            # we've tripped the noise floor, expect incoming signal.
            # monitor the freq until we hit the signal
            if self.sample_data_bit() == 0: # start bit detected!
                async with self.io_lock:
                    pass # read the data now!

    def sample_data_bit(self):
        # gets a single bit based off of a 5ms sample
        sample_list = []
        start_time = time.ticks_ms()
        while time.ticks_diff(time.ticks_ms(), start_time) < 5:
            sample_list.append(self.line_in.read_u16())
            time.sleep_us(100) # ~100us/ sample, aka 10kHz, should be enough for us
        
        zcount = 0 # crossings
        if sample_list[0] > 32768: # what position are we comparing it to.
            zdir = True
        else:
            zdir = False 
        for s in sample_list:
            if zdir:
                if s < 32768 + self.noise_floor:
                    zcount += 1
                    zdir = False
            else:
                if s > 32768 - self.noise_floor:
                    zcount += 1
                    zdir = True 
        # 1800 Hz should do 18 crossings in 5 milliseconds
        # 1400 should do 14
        if zcount > 20: # too high pitched, probaby noise.
            return -1
        elif zcount > 16: # most likely a 0
            return 0 
        elif zcount > 12: # most likely a 1
            return 1
        else:
            return -1 # too few crossings, likely not a real signal.
        
    def read_full_byte(self, byte_start):
        # with the start bet detected at byte_start, sample the data for a full byte.
        # Because it's timing dependent, this will likely block other processes.
        # Let's be honest: we're handling text over an audio coupler, it's fine.
        # start by setting up our needed objects:
        incoming_byte = 0
        bitcount = 0
        waiting_time = 20 - time.ticks_diff(byte_start, time.ticks_ms())
        while bitcount < 5:
            time.sleep_ms(waiting_time) 
            next_bit = self.sample_data_bit()
            if next_bit >=0:
                incoming_byte = (incoming_byte | next_bit) << 1
            else:
                raise IOError # something is up, flag an error.
            bitcount += 1
            waiting_time = 20 + (20 * bitcount) - time.ticks_diff(byte_start, time.ticks_ms())
            
    async def pull_data_buffer(self) -> str:
        # if it's available, return teh buffered data
        return ""

class BaudotInterface:
    def __init__(self, audio_in_pin, audio_out_pin):
        self.incoming_buffer = ""
        self.io_lock = asyncio.Lock() # stop input and output 
        self.input_interface = BaudotInput(audio_in_pin, self.io_lock) #TODO: make this init an input obj
        self.output_interface = BaudotOutput(audio_out_pin) #TODO: make this init an output obj

    async def write(self, string):
        # Push a string to the output buffer, and signal that we are ready to output data
        # Maybe this is the best time to sanitize our inputs?
        self.output_interface.buffer_string(string)
        await self.output_interface.play_data_tones(self.io_lock)
    
    def read(self):
        # Return the data that was in the buffer, and clear it.
        output = self.incoming_buffer
        self.incoming_buffer = ""
        return output 
    
    async def pull_buffered_data(self):
        # pull data from the input object
        # awaitable because it may be busy handling/decoding input
        async with self.io_lock: # lock the input from happening??
            self.incoming_buffer += await self.input_interface.pull_data_buffer()
        
        