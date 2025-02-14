#######
# Baudot MicroPython Thing
# V 0.0.2 
# Abandon all async ye who enter here
####################



from machine import PWM, ADC, Pin #type: ignore 
from micropython import const #type:ignore
from time import ticks_diff, ticks_add, ticks_ms, time #type:ignore
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
    def __init__(self, pin_a, pin_b, max_vol = 2**16, rate = 50):
        # Use stereo output to our advantage: we can mix our PWM signals to make it work betterer?
        self.pwm_mark = PWM(pin_a, freq = 1400, duty_u16 = 0)
        self.pwm_space = PWM(pin_b, freq = 1800, duty_u16 = 0)
        self.active = False 
        self.max_volume = max_vol # allow for volume control
        self.buffer = deque((),280) # if it can fit in a tweet, we can print it in one go
        self.bit_time = int(1000/rate) # 20 for 50 baud, 22 for 45.5

    def start_transmission(self):
        # Begin transmitting, by asserting our mark tone for a few ms
        self.active = True
        end_assert_time = ticks_add(ticks_ms(), 50)
        self.pwm_mark.duty_u16(self.max_volume)
        while ticks_diff(end_assert_time, ticks_ms()) > 0:
            pass


    def send_byte(self, byte):
        # Send an entire data byte as a packet
        start_time = ticks_ms()
        self.pwm_space.duty_u16(self.max_volume) # assert space before deasserting mark, so the device doesn't get confused
        self.pwm_mark.duty_u16(0)
        end_time = ticks_add(start_time, self.bit_time) 
        bcount = 0 # bit counter
        while ticks_diff(end_time, ticks_ms()) > 0:
            pass # delay until our byte is completed.
        while bcount < 5: 
            if (byte >> bcount) & 1:
                self.pwm_mark.duty_u16(self.max_volume)
                self.pwm_space.duty_u16(0)
            else:
                self.pwm_space.duty_u16(self.max_volume)
                self.pwm_mark.duty_u16(0)
            
            bcount += 1
            end_time = ticks_add(ticks_ms(), (self.bit_time * bcount))
            while ticks_diff(end_time, ticks_ms()) > 0:
                pass # wait for the next bit, until we are done.
        # output carrier tone for at least 1.5 bits:
        self.pwm_mark.duty_u16(self.max_volume)
        self.pwm_space.duty_u16(0)
        end_time = ticks_add(end_time, (self.bit_time * 2))
        while ticks_diff(end_time, ticks_ms())> 0:
            pass 
    


    def end_transmission(self):
        # play anti-echo, then return to silent
        end_time = ticks_add(ticks_ms(), 150) # 150 or 300ms, depending on your preference
        while ticks_diff(end_time, ticks_ms()) > 0:
            pass # simply wait, as we should be ending on the 1400hz tone
        self.pwm_mark.duty_u16(0)
        self.active = False

    def send_buffer(self):
        self.start_transmission()
        while len(self.buffer) > 0:
            self.send_byte(self.buffer.popleft())
        self.end_transmission()

    def write(self, text_to_send:str):
        mode = LTRS
        text_to_send = text_to_send.upper()
        # First assert our mode:
        if text_to_send[0] in LTRS:
            self.buffer.append(0x1B)
        else:
            self.buffer.append(0x1F)
            mode = FIGS
        char_count = 1
        # add message to send buffer
        for c in text_to_send:
            if c in mode:
                self.buffer.append(mode.index(c))
            elif c in FIGS:
                mode = FIGS
                self.buffer.append(0x1f)
                self.buffer.append(mode.index(c))
                char_count = 0 # we've asserted recently, so we don't need to again
            elif c in LTRS:
                mode = LTRS
                self.buffer.append(0x1b)
                self.buffer.append(mode.index(c))
                char_count = 0
            else: # replace invalid characters with a space
                self.buffer.append(5) 
            char_count += 1
            if char_count % 15 == 0:
                if mode == LTRS:
                    self.buffer.append(0x1b)
                    char_count = 0
                elif mode == FIGS:
                    self.buffer.append(0x1f)
                    char_count = 0
        # fart that bad boy out audio-style
        self.send_buffer()


class BaudotInput:
    def __init__(self, adc_pin, noise_floor = 1000, rate = 50, monitor_led = False, rx_led = False):
        self.input = ADC(adc_pin)
        self.noise_floor = noise_floor
        self.buffer = "" 
        self.bit_time = int(1000/rate) # 20 for 50 baud, 22 for 45.5
        self.mode = LTRS
        if monitor_led:
            self.monitor_led = Pin(monitor_led)
        else:
            self.monitor_led = False
        if rx_led:
            self.rx_led = Pin(rx_led)
        else:
            self.rx_led = False

    def decode_byte(self, byte):
        decoded = self.mode[byte]
        # Return an empty string for mode switches.
        if decoded == "LTRS":
            self.mode = LTRS
            return ""
        elif decoded == "FIGS":
            self.mode = FIGS
            return ""
        return decoded # or whatever string the byte refers to.

    def take_sample(self) -> bool:
        # Returns a 1 or 0 depending on what the sample is.
        samp_buff = []
        end_time = ticks_add(ticks_ms(), 5)
        # 5ms of samples should be enough, and give us space for re-sampling if needed.
        while ticks_diff(end_time, ticks_ms()) > 0:
            samp_buff.append(self.input.read_u16())
            # ideally i would rate limit this but i think the inherent lag of micropython and the adc read function is enough
            # it's not like 5ms of data is THAT much.......
        zero_count = 0
        low_thresh = 32768 - self.noise_floor
        hi_thresh = 32768 + self.noise_floor
        if samp_buff[0] > 32768:
            look_above = False
        else:
            look_above = True
        for s in samp_buff:
            if s > hi_thresh and look_above:
                zero_count += 1
                look_above = False
            elif s < low_thresh and not look_above:
                zero_count += 1
                look_above = True
        # at 1400 Hz we expect 14 crossings in 5ms
        # 1800 Hz would be 18
        if zero_count < 16:
            return 1 # return a 1 since it is the mark tone
        elif zero_count < 20:
            return 0
        else:
            raise IOError # something didn't compute correctly.
        
    def wait_for_tone(self, timeout = -1):
        # waits for timeout ms or until tone is established.
        end_time = ticks_add(ticks_ms(), timeout)
        time_checked =  ticks_ms()
        while self.take_sample():
            # Check if we've hit the timeout yet.            
            if ticks_diff(end_time, ticks_ms()) < 0 and timeout > 0:
                return False # no sample found.
            # update when we last checked the time
            time_checked =  ticks_ms()
        # if we get here, we've hit an 1800Hz tone.
        # we'll want to know the start time, so return that.
        return time_checked
    
    def read_full_byte(self, start_time):
        # Byte structure is as follows:
        # 1 start bit, 5 data bits, 1.5 stop bits
        # we've already read the start bit, so we need to prepare for the rest:
        data_start_time = ticks_add(start_time, self.rate)
        byte_buffer = 0
        bit_count = 0
        # wait for the next bit to begin.
        while ticks_diff(data_start_time, ticks_ms()) > 0:
            pass 
        while bit_count < 5:
            byte_buffer |= self.take_sample()
            bit_count += 1
            next_bit_time = ticks_add(data_start_time, (bit_count * self.rate))
            byte_buffer = byte_buffer << 1
            while ticks_diff(next_bit_time, ticks_ms()) > 0:
                pass # wait for our next bit
        return byte_buffer # Return our buffered byte
    
    def read_loop(self, timeout):
        loop_timeout = time() + timeout # we only care about the seconds here.
        read_buffer = []
        if self.monitor_led:
            self.monitor_led.value(1) # turn on our monitor light, if we got one
        loop = True
        while loop:
            tone_check = self.wait_for_tone(1000)
            if tone_check: 
                self.rx_led.value(1)
                read_byte = self.read_full_byte(tone_check)
                read_buffer.append(self.decode_byte(read_byte))
                tone_check = False 
                loop_timeout += 1 # add another second to our loop timeout.
            else: # if we don't get a tone before the timeout
                if time() > loop_timeout:
                    break

        
                


        
            
    
    

        

''' THIS IS BROKEN SO SKIP IT
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
    indat = False
    while True:
        if indat == "INPUT" or indat == False:
            give_str = input("INPUT REQUEST: ")
            interface.write(give_str)
        else: 
            print(indat)
        interface.enable_listener() # signal as ready to take incoming data
        await interface.data_rx_event.wait() # wait for incoming data
        interface.pause_listener() # pause the listening proccess until we are done our part
        indat = interface.read()

async def TEST_print_to_console(pin1, pin2):
    interface = BaudotInterface(pin1, pin2)
    task_list = set()
    task_list.add(interface.input_interface.listener())
    task_list.add(interface.output_interface.send_when_ready())
    task_list.add(print_incoming_data(interface))
    return asyncio.gather(task_list) # fire them all off'''
