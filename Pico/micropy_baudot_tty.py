#######
# Baudot MicroPython Thing
# V 0.0.1 
# Maybe, possibly working
####################



from machine import PWM, ADC #type: ignore 
from micropython import const #type:ignore
import time
import asyncio
from collections import deque
from micropython import const #type:ignore

# freq. constants
_BAUDOT_ONE = const(1400) # 1400hz is the mark/carrier tone
_BAUDOT_ZERO = const(1800) # 1800 is space/zero
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

class BaudotOutput:
    def __init__(self, out_pin, iolock, send_event):
        self.output = PWM(out_pin, freq = 1400, duty_u16 = 0) # start muted
        self.buffered_out = deque(())
        self.out_mode = LTRS # what output mode are we in
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
        # blocks further execution because timing is sensitive on this bad boy.
        # IF YOU HAVE ISSUES WITH LONG STRINGS GOING OUT, TRY HERE
        #NOTE: YOU PROBABLY FUCKED UP WITH TIMING HERE
        end_time = time.ticks_add(time.ticks_ms(), duration)
        self.output.freq = value
        self.output.duty_u16(32768) # GIV'R BUD
        while time.ticks_diff(time.ticks_ms(), end_time) > 0:
            pass
            
        self.output.duty_u16(0) # and back to mute

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

    async def send_when_ready(self):
        # Will send queued data if it is ready
        while True:
            await self.rts.wait() 
            if len(self.buffered_out) > 0: # If we have data
                with self.lock: # block anything else from running
                    self.play_data_tones()
            self.rts.clear() # Let the queue build up again

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
                bit_start = time.ticks_ms() # just get the tick value for when this was.
                data_timeout = time.ticks_add(time.ticks_ms(), 100) # 100 ms timeout before we yield to other processes.
                # we've tripped the noise floor, expect incoming signal.
                # monitor the freq until we hit the signal
                async with self.io_lock: # lock anything else from interrupting
                    while time.ticks_diff(time.ticks_ms(), data_timeout) > 0:   
                        sample_bit = self.sample_data_bit()
                        if sample_bit == 0: # If we get a start bit
                            if self.read_full_byte(bit_start):
                                # if there's successful data transfer, move the timeout
                                bit_start = time.ticks_add(bit_start, 150)
                                # after we get real data, use a 500ms timeout instead
                                data_timeout = time.ticks_add(time.ticks_ms(), 500) 
                                # let other funky shit happen while we wait for the next bit
                                # ticks_diff will give us an approximate time, so maybe we should drop it by a little bit?
                                #NOTE: IF YOU GET A BUNCH OF ISSUES WITH LONG STRINGS, TRY FUCKING WITH THIS
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
        sample_timeout = time.ticks_add(time.ticks_us(), 5000)
        while time.ticks_diff(sample_timeout, time.ticks_us()) > 0:
            sample_list.append(self.line_in.read_u16())
            time.sleep_us(50) # ~60us/ sample, should be enough for us
        
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
            waiting_time = 20 + (20 * bitcount)
            next_time = time.ticks_add(byte_start, waiting_time)
            while time.ticks_diff(next_time, time.ticks_ms()) > 0:
                pass # idle until we're ready for the next bit
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
        self.trigger_sender.set()
    
    def read(self):
        # Return the data that was in the buffer, and clear it.
        output = self.incoming_buffer
        self.incoming_buffer = ""
        return output 
    
    def enable_listener(self):
        # flags the listener event to be able to run
        self.trigger_listener.set()

    def pause_listener(self):
        # flags the listener to idle until allowed
        # softer than the io lock since we can still output data
        # useful if you want to delay part of a message for whatever reason
        self.trigger_listener.clear()
        

    async def pull_buffered_data(self):
        # pull data from the input object
        # awaitable because it may be busy handling/decoding input
        async with self.io_lock: # this won't let it run if we're waiting on more data to arrive
            self.incoming_buffer += self.input_interface.pull_data_buffer()


# Functions for testing/demo below.

async def print_incoming_data(interface:BaudotInterface):
    while True:
        interface.enable_listener() # signal as ready to take incoming data
        await interface.data_rx_event.wait() # wait for incoming data
        interface.pause_listener() # pause the listening proccess until we are done our part
        indat = interface.read()

        if indat == "INPUT":
            give_str = input("INPUT REQUEST:")
            interface.write(give_str)
        else: 
            print(interface.read())
        

def TEST_print_to_console(pin1, pin2):
    interface = BaudotInterface(pin1, pin2)
    task_list = set()
    task_list.add(interface.input_interface.listener())
    task_list.add(interface.output_interface.send_when_ready())
    task_list.add(print_incoming_data(interface))
    asyncio.gather(task_list) # fire them all off
