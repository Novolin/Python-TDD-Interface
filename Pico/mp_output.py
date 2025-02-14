# I'm overwhelmed with a few things so I want to get a basic, functional output working first.
from machine import PWM #type:ignore
from time import ticks_ms, ticks_add, ticks_diff 
from collections import deque

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
    def __init__(self, pin_a, pin_b, max_vol = 2**16):
        # Use stereo output to our advantage: we can mix our PWM signals to make it work betterer?
        self.pwm_mark = PWM(pin_a, freq = 1400, duty_u16 = 0)
        self.pwm_space = PWM(pin_b, freq = 1800, duty_u16 = 0)
        self.active = False 
        self.max_volume = max_vol # allow for volume control
        self.buffer = deque((),280) # if it can fit in a tweet, we can print it in one go

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
        end_time = ticks_add(start_time, 20) 
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
            end_time = ticks_add(ticks_ms(), (20 * bcount))
            while ticks_diff(end_time, ticks_ms()) > 0:
                pass # wait for the next bit, until we are done.
        # output carrier tone for at least 30ms:
        self.pwm_mark.duty_u16(self.max_volume)
        self.pwm_space.duty_u16(0)
        end_time = ticks_add(end_time, 30)
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
            
                



