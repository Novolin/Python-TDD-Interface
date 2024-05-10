# TTY/TDD Interface
This project is an attempt to allow users to interface with an Ultratec Superprint 4425, using Baudot encoding.

Eventually, it will support two-way communication, but currently, it is focused on host -> tty output. 

It should be compatible with other Baudot-based TTY solutions, as long as the carrier tones/communication rates are the same. (1400/1800 Hz, 45.5 or 50 baud)

For direct interfacing, upload the files in /Pico to a Pi Pico, or other CircuitPython-compatible microcontroller. 

To use discrete .wav files for each message, use tty_encoder.py. I'll write more instructions once it's actually working properly!




# Required Libraries:
* [Pydub:](https://github.com/jiaaro/pydub)
    * handles audio encoding for wav files, not needed for Pico


## Known Issues:
# Major issues:
* Hardware ain't workin (Pico)
    - Waiting on parts
* Documentation incomplete
* Decoding not implemented
    * I know *what* to do, but not *how* to do it, yet!

# Tweaks:
- UI needs polish
- Data packet length needs some tweaking ( make sure each packet is 300ms?)
- files need cleanup
- harsh transitions between bits in 45.5 baud
    

# Changelog:
## V0.03:
* Fixed byte-flipping issue with FSK encoding
* Made a GUI for the encoding application.
* Tweaked audio files for smoother playback
* Various minor fixes. See docs/changelog.txt

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

