## Project Roadmap
This is a todo list/general concept graveyard:

# Ideal goals
Interface with a computer terminal via TDD
Failing that, have a TDD-based text game engine that can run on a Raspberry Pi Pico or similar hardware.

# Hardware phase:
Design prototype hardware to send and recieve audio via TTY

Use Pi Pico to read audio from TTY, decode FSK audio

Connect to speaker and play PWM audio

# Software Phase:

Encode data in 50 baud TTY-compatible FSK

Decode data from same (Not started, hard :( )

Encode audio files which can transport data to TTY (portability?)

Decode recorded audio (Also backup, largely for learning)

Switch from .wav files with tones to proper frequency generation (maybe)

