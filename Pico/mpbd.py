#######
# Baudot MicroPython Thing
# V 0.0.3 
# return of the pwm
####################

# if this works better im gonna shit
# may need a cap in line with the speaker

from machine import PWM, ADC, Pin #type: ignore 
from time import ticks_diff, ticks_add, ticks_ms, ticks_us, time #type:ignore
from collections import deque
from math import tau, sin
from micropython import const #type: ignore

# PWM Sine Table Stuff
TABLE_LENGTH = 20 # 20 samples per wave
_MAXVOL = 2**12 
SINE_TABLE = [
    int(32768 + _MAXVOL * sin((tau / TABLE_LENGTH)* i)) for i in range(TABLE_LENGTH)
]
# how many us per step in the pwm signal (@ 20 samples/wave. recalc if you change that.)
MARK = const(36) 
SPACE = const(28)




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

# The primary difference for this one is I'm trying to use PWM properly to control pseudo-analog voltage
# The other one just uses square waves and hopes for the best.


class BaudotOutput:
    def __init__(self, pwm_pin, rate = 50):
        # Use stereo output to our advantage: we can use one channel for each frequency
        self.pwm = PWM(pwm_pin, freq = 10000, duty_u16 = 0) 
        self.mode = LTRS
        self.active = False 
        self.buffer = deque((),280) # if it can fit in a tweet, we can print it in one go
        self.bit_time =  int(1000/rate) # 20ms for 50 baud, 22ms for 45.5
        self.assert_every = 30 # how many characters we should wait before reasserting mode
        self.since_assert = 99

    def do_tone(self, tone, length:int):
        ''' plays tone (either MARK or SPACE) for length ms'''
        sinestep = 0
        end_time = ticks_add(ticks_us(), length * 1000) #convert ms to us
        while ticks_diff(end_time, ticks_us()) > 0:
            next_step = ticks_add(ticks_us(), tone)
            self.pwm.duty_u16 = SINE_TABLE[sinestep]
            sinestep += 1
            if sinestep >= TABLE_LENGTH:
                sinestep = 0
            while ticks_diff(next_step, ticks_us()) > 0:
                pass # wait for the next pwm step.
        
    
    def start_transmission(self):
        # Begin transmitting, by asserting our mark tone for a 150ms (per the standard)
        self.active = True
        self.do_tone(MARK, 150)


    def send_byte(self, byte):
        ''' Sends a singe byte of data, including start and stop bits'''
        self.do_tone(SPACE, self.bit_time)
        for i in range(6):
            if (byte >> i) & 1:
                self.do_tone(MARK, self.bit_time)
            else:
                self.do_tone(SPACE, self.bit_time)
        self.do_tone(MARK, int(self.bit_time * 1.5)) # stop bit is 1.5x the regular bit
        
        
    
    def end_transmission(self):
        # play anti-echo, then return to silent
        self.do_tone(MARK, 150)
        self.pwm.duty_u16(0)
        self.active = False

    def send_buffer(self):
        self.start_transmission()
        while len(self.buffer) > 0:
            self.send_byte(self.buffer.popleft())
        self.end_transmission()

    def sanitize_string(self, string:str, override_str:str = " ", newline = "\n\r") -> str:
        ''' Sanitizes the input string to work with baudot encoding, encodes new lines to work nicely, too.'''
        outstr = ""
        for c in string.upper():
            if c == "\n":
                outstr += newline
            elif c in LTRS or c in FIGS:
                outstr += c
            else:
                outstr += override_str

    def buffer_string(self, string):
        ''' adds a string to the buffer to send.'''
        for c in string:
            if c not in self.mode or self.since_assert > self.assert_every:
                if c in LTRS:
                    self.mode = LTRS
                    self.buffer.append(0x1B)
                    self.since_assert = 0
                elif c in FIGS:
                    self.mode = FIGS
                    self.buffer.append(0x1F)
                    self.since_assert = 0
                else: # if the string isn't sanitized properly
                    print("Invalid Character: " + c)
                    self.buffer.append(0x04)
                    continue # don't try to add a junk character
            self.buffer.append(self.mode.index(c))
            self.since_assert += 1

    def write(self, text_to_send:str):
        # sanitize our input:
        sanistring = self.sanitize_string(text_to_send)
        # buffer it:
        self.buffer_string(sanistring)
        # send it:
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

    def decode_byte(self, byte) -> str:
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
            return True # return a 1 since it is the mark tone
        elif zero_count < 20:
            return False
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
    
    def read_full_byte(self, start_time) -> int:
        # Byte structure is as follows:
        # 1 start bit, 5 data bits, 1.5 stop bits
        # we've already read the start bit, so we need to prepare for the rest:
        data_start_time = ticks_add(start_time, self.bit_time)
        byte_buffer = 0
        bit_count = 0
        # wait for the next bit to begin.
        while ticks_diff(data_start_time, ticks_ms()) > 0:
            pass 
        while bit_count < 5:
            byte_buffer |= self.take_sample()
            bit_count += 1
            next_bit_time = ticks_add(data_start_time, (bit_count * self.bit_time))
            byte_buffer = byte_buffer << 1
            while ticks_diff(next_bit_time, ticks_ms()) > 0:
                pass # wait for our next bit
        return byte_buffer # Return our buffered byte
    
    def read_loop(self, timeout):
        loop_timeout = time() + timeout # we only care about the seconds here.
        read_buffer = []
        if type(self.monitor_led) == Pin: 
            self.monitor_led.value(1) # turn on our monitor light, if we got one
        loop = True
        while loop:
            tone_check = self.wait_for_tone(1000)
            if tone_check: 
                if type(self.rx_led) == Pin:
                    self.rx_led.value(1)
                read_byte = self.read_full_byte(tone_check)
                self.buffer += self.decode_byte(read_byte)
                tone_check = False 
                loop_timeout += 1 # add another second to our loop timeout.
            else: # if we don't get a tone before the timeout
                if time() > loop_timeout:
                    loop = False
        
    def read(self):
        # output the buffered text, and display it.
        output = self.buffer
        self.buffer = ""
        return output
    