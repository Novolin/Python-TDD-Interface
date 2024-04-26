# TTY Terminal
This project is an attempt to make a terminal interface via a Ultratec Superprint 4425, using Baudot encoding.

Eventually, it will support two-way communication, but currently, it is focused on host -> tty output. 

It should be compatible with other Baudot-based TTY solutions, as long as the carrier tones/communication rates are the same.


# Changelog:
## V0.01: 
* Modified code from [John Park's TTY Project](https://learn.adafruit.com/clue-teletype-transmitter/code-the-tty-transmitter) to be importable
* Began echoing serial input over TTY