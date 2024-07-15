# testing fsk decoding on the pico

import board
from analogio import AnalogIn
import analogbufio
import array
from supervisor import ticks_ms
from time import sleep



class TTYReader:
    def __init__(self, pin, baudrate):
        self.baudrate = baudrate
        self.pin = pin
        self.in_buff = array.array("H", [0]*80) # 80 samples = 10 ms
        self.analog_reader = False
        self.incoming_data = "" # String recieved from the TTY
        self.zero_point = 0

    def init_monitor(self):
        self.deinit_reader() # make sure there isn't already something running
        self.analog_reader = AnalogIn(self.pin)
        
    def deinit_reader(self):
        try:
            self.analog_reader.deinit()
        except:
            print("No reader to deinitialize. Continuing.")
        self.analog_reader = False
        return

    def check_for_silence(self, threshold = 200):
        if self.analog_reader.value > threshold:
            # WE GOT A BYTE!
            return True
        return False # no noise :)

    def read_data(self):
        self.analog_reader.readinto(self.in_buff)
        return self.in_buff

    def init_reader(self):
        self.deinit_reader()
        self.analog_reader = analogbufio.BufferedIn(self.pin, sample_rate = 8000) # 8kHz sample rate, we don't need a super high res?


    def get_sampled_freqency(self):
        # Count zero crossings in our sample
        zero_crossings = 0
        current_sign = 1
        for sample in self.in_buff:
            if sample * current_sign < 0:
                zero_crossings += 1
                current_sign = current_sign * -1
        # do some basic math:
        if zero_crossings > 32:
            return 0 # 1800
        else:
            return 1 # 1400
        
    def read_full_byte(self):
        # Read an entire byte of data:
        byte_buffer = 0
        self.init_reader()
        start_time = ticks_ms()
        for b in range(6):    
            self.read_data()
            byte_buffer &= self.get_sampled_frequency()
            byte_buffer = byte_buffer << 1
            while ticks_ms() < start_time + (b * 20):
                pass # wait for next bit to start
        return byte_buffer

    def calibrate(self):
        pass


class TTYReader2:
    # redo that should work better now

    def __init__(self, pin, baudrate):
        self.pin = pin
        self.analog_input = False # Wait for something to initialize it
        self.input_buffer = array.array("H",[0] * 100) #10ms of samples
        self.baudrate = baudrate
        self.bit_time = 20
        if baudrate == 45:
            self.bit_time = 22
        self.silence_level = 30
        self.noise_floor = 10
        self.await_bit = True #are we waiting on the line to do something
        self.calibrate()
        self.recieved_string = ""
        self.read_byte_arr = bytearray([0] * 32) # 32 bytes should be enough?
        self.byte_pointer = 0 # which byte we're messing with in the array
        self.byte_start_time = 0 # When the last byte was read, just in case we need to do weird shit later.
        

    def init_monitor(self):
        if self.analog_input != False:
            self.analog_input.deinit()
        self.analog_input = AnalogIn(self.pin)
        self.await_bit = True
        return
    
    def init_reader(self):
        if self.analog_input != False:
            self.analog_input.deinit()
        self.analog_input = analogbufio.BufferedIn(self.pin, sample_rate = 10000) #10kHz for easier math, and more samples = more accurate data
        return
    
    def calibrate(self):
        print("Calibrating Analog Input...")
        self.init_reader()
        self.analog_input.readinto(self.input_buffer)
        self.silence_level = sum(self.input_buffer)//100 # we know we have 100 samples. Use integers to make math faster, since timing is important
        if self.silence_level > 3000 or self.silence_level == 0:
            print("Calibration error! Aborting!")
            return False
        else: 
            print("Calibrated! Silence threshold = " + str(self.silence_level))
            print("Beginning Monitor...")
            self.init_monitor()

            return True

    
    def read_bit_get_value(self):
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

        if zero_crossings > 32: # > 1600 hz
            return False
        else:
            return True

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
        
    def check_for_input(self): # Returns false when input detected.
        check = self.analog_input.value
        if check > self.silence_level + self.noise_floor or check < self.silence_level - self.noise_floor:
            return False 
        return True 
    




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
                self.decode_byte_array()

            if last_read_byte == 8 or byte_timeout > ticks_ms():
                # This is a carriage return character, for now we will let this be the end of the message
                # TODO: handle this properly so a message can contain CRs.
                continue_monitoring = False
            
        self.decode_byte_array() # decode any text we've hit
        # we're free of the loop! 
        return self.recieved_string 
            
    def decode_byte_array(self): # NOT IMPLEMENTED YET! WILL DECODE BYTE ARRAY, RESET POINTER.
        return "TODO"                

