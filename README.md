# TTY Terminal
This project is an attempt to make a terminal interface via a Ultratec Superprint 4425, using Baudot encoding.

Eventually, it will support two-way communication, but currently, it is focused on host -> tty output. 

It should be compatible with other Baudot-based TTY solutions, as long as the carrier tones/communication rates are the same.


# Required Libraries:
* Pydub: (put a link here)
    * handles audio encoding for bd_encode.py

# Changelog:
## V0.02:
I'm waiting on some hardware for the audio side of things so I did some non-circuitpython scripting: 

* Added audio encoding script
    * Exports strings as an FSK - encoded .wav
    * Will have a version that decodes once I learn how to do frequency analysis

* Began work on a rudimentary game engine
    * Simple text parsing system
    * mostly experimental, will likely change/be re-written at some point
    * Maybe find a way to integrate something with an existing dev framework

## V0.01: 
* Modified code from [John Park's TTY Project](https://learn.adafruit.com/clue-teletype-transmitter/code-the-tty-transmitter) to be importable
* Began echoing serial input over TTY

