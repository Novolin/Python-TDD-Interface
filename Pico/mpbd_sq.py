#######
# Baudot MicroPython Thing
# V 0.0.2b
# Square Waves and Timing Changes
####################



from machine import PWM, ADC, Pin #type: ignore 
from time import ticks_diff, ticks_add, ticks_ms, ticks_us, time #type:ignore
from collections import deque


# Character encodings
LTRS = (
    "\b",   #0b00000 0x00
    "E",    #0b00001 0x01
    "\n",   #0b00010 0x02
    "A",    #0b00011 0x03
    " ",    #0b00100 0x04
    "S",    #0b00101
    "I",    #0b00110
    "U",    #0b00111
    "\r",   #0b01000
    "D",    #0b01001
    "R",    #0b01010
    "J",    #0b01011
    "N",    #0b01100
    "F",    #0b01101
    "C",    #0b01110
    "K",    #0b01111
    "T",    #0b10000
    "Z",    #0b10001
    "L",    #0b10010
    "W",    #0b10011
    "H",    #0b10100
    "Y",    #0b10101
    "P",    #0b10110
    "Q",    #0b10111
    "O",    #0b11000
    "B",    #0b11001
    "G",    #0b11010
    "FIGS", #0b11011
    "M",    #0b11100
    "X",    #0b11101
    "V",    #0b11110
    "LTRS", #0b11111
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
    def __init__(self, pin_a, pin_b, max_vol = 2**15, rate = 50):
        # Use stereo output to our advantage: we can use one channel for each frequency
        self.pwm_mark = PWM(pin_a, freq = 1400, duty_u16 = 0)
        self.pwm_space = PWM(pin_b, freq = 1800, duty_u16 = 0)
        self.mode = LTRS
        self.active = False 
        self.max_volume = max_vol # allow for volume control
        self.buffer = deque((),280) # if it can fit in a tweet, we can print it in one go
        self.bit_time =  int(1000000/rate) # 20ms for 50 baud, 22ms for 45.5
        self.assert_every = 30 # how many characters we should wait before reasserting mode
        self.since_assert = 99

    def start_transmission(self):
        # Begin transmitting, by asserting our mark tone for a few ms
        self.active = True
        end_assert_time = ticks_add(ticks_ms(), 150)
        self.pwm_mark.duty_u16(self.max_volume)
        while ticks_diff(end_assert_time, ticks_ms()) > 0:
            pass


    def send_byte(self, byte):
        # Send an entire data byte as a packet
        bcount = 0 # bit counter
        start_time = ticks_add(ticks_us(), 10000) # give a 10 ms buffer, because i dont trust like that
        timearray = []
        for i in range(8):
            timearray.append(ticks_add(start_time, self.bit_time + (self.bit_time * i)))
        self.pwm_mark.duty_u16(0)
        self.pwm_space.duty_u16(self.max_volume) # assert space before deasserting mark, so the device doesn't get confused
        end_time = ticks_add(ticks_us(), self.bit_time) 
        while ticks_diff(end_time, ticks_us()) > 0:
            pass # delay until our bit is completed.
        while bcount < 6: 
            if (byte >> bcount) & 1:
                self.pwm_space.duty_u16(0)
                self.pwm_mark.duty_u16(self.max_volume)
            else:
                self.pwm_mark.duty_u16(0)
                self.pwm_space.duty_u16(self.max_volume)
            bcount += 1
            while ticks_diff(timearray[bcount + 1], ticks_us()) > 0:
                pass # wait for the next bit, until we are done.
        # output carrier tone for at least 1.5 bits:
        self.pwm_space.duty_u16(0)
        self.pwm_mark.duty_u16(self.max_volume)

        end_time = ticks_add(end_time, (30000))
        while ticks_diff(end_time, ticks_us())> 0:
            pass 
    
    def end_transmission(self):
        # play anti-echo, then return to silent
        end_time = ticks_add(ticks_ms(), 300) # 150 to 300ms, depending on your preference
        while ticks_diff(end_time, ticks_ms()) > 0:
            pass # simply wait, as we should be ending on the 1400hz tone
        self.pwm_mark.duty_u16(0)
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
        return outstr

    def buffer_string(self, string:str):
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
        ''' why do this in multiple '''
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
    