# just cleaning up based on what i've learned
# add some better comments here, nerd!



from machine import PWM, ADC #type: ignore 
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
    def __init__(self, out_pin, iolock, send_event):
        self.output = PWM(out_pin, freq = 16000)
        self.buffered_out = deque(())
        self.out_mode = LTRS # what output mode are we in
        self.sample_position = 0 # where in the sine table are we. Used for smooth transitions between freqencies.
        self.rts = send_event # ready to send event
        self.lock = iolock

    def buffer_string(self, string_to_buffer:str):
        # Adds string to the output buffer
        # Ensure we end with a newline
        if string_to_buffer[-1] != "\n":
            string_to_buffer += "\n"
        char_count = 0 # a counter to know when to reassert LTRS/FIGS             
        for c in string_to_buffer: 
            # First check if we need to assert mode:
            if char_count % 10 ==  0 or c not in self.out_mode: # reassert every 10 chars sent.
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
            time.sleep(value)

    def play_data_tones(self): 
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
        return True # sent queued data

    async def send_if_ready(self):
        # Will send queued data if it is ready
        await self.rts.wait() 
        if len(self.buffered_out) > 0: # If we have data
            with self.lock: # block anything else from running
                self.play_data_tones()

class BaudotInput:
    def __init__(self, adc_pin, io_lock, allow_event, rx_event):
        self.line_in = ADC(adc_pin)
        self.read_mode = LTRS # default to reading in LTRS mode
        self.data_buffer = "" # buffer for incoming data
        self.noise_floor = 1024 # how much noise on the line before we detect signal
        self.io_lock = io_lock
        self.new_input = rx_event
        self.input_error = asyncio.Event() # idk if this is the best way to do it but whatevzzzz
        self.allow_listen = allow_event

    async def listener(self):
        # continually listens for tone, writes new data to the input buffer
        while True:
            await self.allow_listen.wait() # wait for the ready-to-listen event to fire
            sample = self.line_in.read_u16()
            if sample > 32768 + self.noise_floor or sample < 32768 - self.noise_floor:
                bit_start = time.ticks_ms() # flag when it happened
                data_timeout = time.ticks_add(bit_start, 100) # 100 ms timeout before we yield to other processes.
                # we've tripped the noise floor, expect incoming signal.
                # monitor the freq until we hit the signal
                async with self.io_lock: # lock anything else from interrupting
                    while time.ticks_ms() < data_timeout:   
                        sample_bit = self.sample_data_bit()
                        if sample_bit == 0: # If we get a start bit
                            if self.read_full_byte(bit_start):
                                # if there's successful data transfer, move the timeout
                                bit_start = time.ticks_add(bit_start, 150)
                                # after we get real data, use a 500ms timeout instead
                                data_timeout = time.ticks_add(time.ticks_ms(), 500) 
                                # let other funky shit happen while we wait for the next bit
                                await asyncio.sleep_ms(time.ticks_diff(time.ticks_ms(), bit_start)) #type:ignore
                            else:
                                self.input_error.set()
                        elif sample_bit == 1: # If it's just our carrier, yield for 5ms
                            await asyncio.sleep_ms(5) #type:ignore
                        else: # Uh oh, error town!
                            self.input_error.set()
                    # We've hit timeout now, so all data should be receieved.
                    # Let's yield to allow the other stuff to go ahead
                    self.allow_listen.clear()
            else: # sample isn't above our floor, so we can wait
                await asyncio.sleep_ms(1) #type:ignore    

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
        while bitcount < 5:
            waiting_time = 20 + (20 * bitcount) - time.ticks_diff(byte_start, time.ticks_ms())
            time.sleep_ms(waiting_time)
            bitcount += 1    
            next_bit = self.sample_data_bit()
            if next_bit >=0: # if we get a 0 or 1
                incoming_byte = (incoming_byte | next_bit) << 1
            else:
                self.input_error.set() # notify that there's an input error.
                return False
        # we have time now to decode, since there's ~30ms to the next bit starting
        
        next_char = self.read_mode[incoming_byte] # check if it's a switching statement
        if next_char == "LTRS":
            self.read_mode = LTRS
        elif next_char == "FIGS":
            self.read_mode = FIGS
        else:
            self.data_buffer += next_char # we can concat a string to a string, it's fine.
        return True 
              
    def pull_data_buffer(self) -> str:
        val = self.data_buffer
        self.data_buffer = ""
        return val

class BaudotInterface:
    def __init__(self, audio_in_pin, audio_out_pin):
        self.incoming_buffer = ""
        self.outgoing_buffer = ""
        self.io_lock = asyncio.Lock() # stop input and output 
        self.trigger_listener = asyncio.Event() # event to tell the listener to go ahead
        self.trigger_sender = asyncio.Event() # event to trigger the sending interface to go ahead
        self.data_rx_event = asyncio.Event()
        self.input_interface = BaudotInput(audio_in_pin, self.io_lock, self.trigger_listener, self.data_rx_event) 
        self.output_interface = BaudotOutput(audio_out_pin, self.io_lock, self.trigger_sender)



    def write(self, string):
        # Push a string to the output buffer, and signal that we are ready to output data
        self.output_interface.buffer_string(string)
        
        
    
    def read(self):
        # Return the data that was in the buffer, and clear it.
        output = self.incoming_buffer
        self.incoming_buffer = ""
        return output 
    
    async def pull_buffered_data(self):
        # pull data from the input object
        # awaitable because it may be busy handling/decoding input
        async with self.io_lock: # this won't let it run if we're waiting on more data to arrive
            self.incoming_buffer += self.input_interface.pull_data_buffer()
        
    async def run_loop(self):
        # This loop will execute until something kills the running flag.
        # it is awaitable so other processes can yield to it when needed.
        pass
        