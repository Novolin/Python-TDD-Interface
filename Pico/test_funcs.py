import board
from digitalio import DigitalInOut, Pull
import baudot_tty as bd
import pico_fsk as fsk
from supervisor import ticks_ms
import array

# Setup a reader/writer element

in_test = fsk.TTYReader(board.A2, 50)
status_led = DigitalInOut(board.GP5)
status_led.switch_to_output()
status_led.value = False

test_arr = array.array("H", [0] * 200)

def input_test():
    print("Make Noise while light lit:")
    status_led.value = True
    in_test.init_reader()
    in_test.analog_input.readinto(test_arr)
    status_led.value = False
    print(test_arr)