# V0.01 - Hopefully a working basic interface.

import time
import board
import usb_cdc 
import baudot_tty as bd # Wow!! Importing code makes it way less messy! Who woulda thunk!




serial = usb_cdc.data

enable_terminal = True
serial_text_buffer = "\n\r" # Use a newline character as default to ensure that it prints properly

max_line_length = 24 # +1 because newline!!!!




import usb_cdc

serial = usb_cdc.console

enable_terminal = True

serial_text_buffer = "\n\r"
serial_max_length = 24

def send_serial_buff():
    global serial_text_buffer
    print(serial_text_buffer)
    bd.send_message(serial_text_buffer)
    serial_text_buffer = "\n\r"


if usb_cdc.Serial.connected:
    print("READY")
while enable_terminal:
    while serial.in_waiting > 0:
        readbyte = serial.read(1)
        if readbyte == "\r":
            send_serial_buff()
        else:
            serial_text_buffer += readbyte.decode('ascii')
            if len(serial_text_buffer) > serial_max_length:
                send_serial_buff()

# idk how doable it is to do fsk decoding on a pico if i dont know how to do it on a full ass pc yet lmao
