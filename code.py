# V0.01 - Hopefully a working basic interface.

import time
import board
import usb_cdc 
import baudot_tty as bd # Wow!! Importing code makes it way less messy! Who woulda thunk!




serial = usb_cdc.data

enable_terminal = True
serial_text_buffer = "\n" # Use a newline character as default to ensure that it prints properly

max_line_length = 25 # +1 because newline!!!!




while enable_terminal: # I think i can make it closable if i do it like this?
    while serial.in_waiting() > 0: # If there's anything waiting in the serial buffer:
        readbyte = serial.read(1)
        if readbyte == b"\r": # Send on carriage return character
            bd.send_message(serial_text_buffer)
            serial_text_buffer = "\n"

        else:
            serial_text_buffer += str(readbyte)
            if len(serial_text_buffer) > max_line_length: # If we hit the end of line, automatically send it to the printer
                bd.send_message(serial_text_buffer)
                serial_text_buffer = "\n"
        
            



