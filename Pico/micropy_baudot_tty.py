#######
# Baudot MicroPython Thing
# V 0.0.2 
# Abandon all async ye who enter here
####################



from machine import PWM, ADC, Pin #type: ignore 
from time import ticks_diff, ticks_add, ticks_ms, time #type:ignore
from collections import deque


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
    def __init__(self, pin_a, pin_b, max_vol = 2**15, rate = 50):
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
    