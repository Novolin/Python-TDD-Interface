# 

import time
import board
import usb_cdc 
import baudot_tty as bd # Wow!! Importing code makes it way less messy! Who woulda thunk!


# TODO: ADD INPUT STUFF
# ALSO DO ANYTHING MORE THAN THE BARE FUCKIN MINIMUM
# this will be broken rn so w/e 
serial = usb_cdc.data
usb_cdc.enable(console=True) # Open a console
enable_terminal = True
serial_buffer = ""
while enable_terminal: # I think i can make it closable if i do it like this?
    while serial.in_waiting() > 0: # If there's anything waiting in the serial buffer:
        readbyte = serial.read(1)
        if readbyte == b"\r":
            pass # This is where you flag it to send the text
        else:
            serial_buffer += readbyte.decode()
            



