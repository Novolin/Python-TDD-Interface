# testing fsk decoding on the pico

import board
from analogio import AnalogIn
import analogbufio
import array
from supervisor import ticks_ms
from time import sleep

class TTYReader:
    # redo that should work better now

    def __init__(self, pin, baudrate):
        self.pin = pin
        self.analog_input = False # Wait for something to initialize it
        self.input_buffer = array.array("H",[0] * 100) # 5 ms of samples
        self.baudrate = baudrate
        self.bit_time = 20
        if baudrate == 45:
            self.bit_time = 22
        self.silence_level = 30
        self.noise_floor = 10
        self.await_bit = True #are we waiting on the line to do something
        self.calibrate()
        self.received_string = ""
        self.read_byte_arr = bytearray([0] * 32) # 32 bytes should be enough?
        self.byte_pointer = 0 # which byte we're messing with in the array
        self.byte_start_time = 0 # When the last byte was read, just in case we need to do weird shit later.
        self.LTRS = (
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
            "LTRS"
            )
        
        self.FIGS = (
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
            "LTRS"
            )
        self.char_mode = self.LTRS # default to letter mode

    def init_monitor(self): # Prepare the analog input pin for one-shot reads
        if self.analog_input != False:
            self.analog_input.deinit()
        self.analog_input = AnalogIn(self.pin)
        self.await_bit = True
        return

    def check_for_input(self): # Returns false when input detected.
        check = self.analog_input.value
        if check > self.silence_level + self.noise_floor or check < self.silence_level - self.noise_floor:
            return False 
        return True     


    def init_reader(self): # Prepare the analog input pin for buffered reads
        if self.analog_input != False:
            self.analog_input.deinit()
        self.analog_input = analogbufio.BufferedIn(self.pin, sample_rate = 20000) 
        return
    
    def calibrate(self):
        print("Calibrating Analog Input...")
        self.init_reader()
        self.analog_input.readinto(self.input_buffer)
        self.silence_level = sum(self.input_buffer)//100 # we know we have 100 samples, and don't need the precision of a proper decimal
        if self.silence_level > 3000 or self.silence_level == 0:
            print("Calibration error! Aborting!")
            return False
        else: 
            print("Calibrated! Silence threshold = " + str(self.silence_level))
            print("Beginning Monitor...")
            self.init_monitor()
            return True

    
    def read_bit_get_value(self):
        tries = 0
        while tries < 2:
            self.analog_input.readinto(self.input_buffer)
            # Count zero crossings in our sample
            zero_crossings = 0
            above_avg = True
            if self.input_buffer[0] < self.silence_level:
                above_avg = False
            for i in self.input_buffer:
                if above_avg and i < self.silence_level:
                    zero_crossings += 1
                    above_avg = False
                elif i > self.silence_level and not above_avg:
                    zero_crossings += 1
                    above_avg = True

            # Do the math for frequency, returning a bool 1 or 0

            if zero_crossings > 17: # > 1600 hz
                return False
            elif zero_crossings < 15:
                return True
            # If we're not returning an appropriate value, something got messed up, try reading again
            tries += 1
            if tries >= 4:
                print("ERROR! BAD DATA INPUT!")
                raise InterruptedError
            
    def read_next_byte(self):
        self.byte_start_time = ticks_ms() # set when the last byte started
        byte_buff = 0
        next_bit = ticks_ms() + self.bit_time
        for i in range(6):
            byte_buff &= self.read_bit_get_value()
            byte_buff = byte_buff << 1
            while next_bit > ticks_ms():
                pass # wait for the next tick!
            next_bit = ticks_ms() + self.bit_time
        return byte_buff
        
    def decode_byte_array(self): # Decode the bytes in the byte array, returning their value. 
	# Note: This will also empty the byte array, and reset the pointer!
        output_str = ""
        for i in self.read_byte_arr:
            if i == 0b11111: # Hard-coded FIGS/LTRS switch because fuck itttttt
                self.char_mode = self.FIGS
            elif i == 0b10101:
                self.char_mode = self.LTRS
            else:
                output_str += self.char_mode[i]
        self.byte_pointer = 0		
        return output_str

  
    def monitor_loop(self):
        byte_timeout = 0
        continue_monitoring = self.calibrate() # If we fail to calibrate, it will not fire
        if not continue_monitoring:
            print("Calibration Error!! Aborting...")
            return -1
        self.await_bit = True
        while continue_monitoring:
            while self.await_bit:
                if not self.check_for_input(): # We have detected input at this point. Begin looking for the data
                    self.await_bit = False
                    self.init_reader()
                    byte_timeout = ticks_ms() + 10000
            # Wait for an 1800 Hz signal
            if not self.read_bit_get_value():
                byte_timeout = ticks_ms() + 10000 # give 10 seconds between each input in case we are slow to type
                # Bit started! Begin reading:
                last_read_byte = self.read_next_byte()
                self.read_byte_arr[self.byte_pointer] = last_read_byte
                self.byte_pointer += 1

                while ticks_ms() < self.byte_start_time + self.bit_time:
                    pass # wait for the next byte to be possible.

            if self.byte_pointer > 31: # we're at the end of the byte buffer, we gotta do somethin!!
                self.received_string += self.decode_byte_array()

            if last_read_byte == 8 or byte_timeout < ticks_ms():
                # This is a carriage return character, for now we will let this be the end of the message
                # TODO: handle this properly so a message can contain CRs.
                continue_monitoring = False
            
        self.received_string += self.decode_byte_array() # decode any text we've hit
        # we're free of the loop! 
        return self.received_string 
            
