# SPDX-FileCopyrightText: 2020 John Park for Adafruit Industries
#
# SPDX-License-Identifier: MIT

### Baudot TTY Message Transmitter

### The 5-bit mode is defined in ANSI TIA/EIA-825 (2000)
### "A Frequency Shift Keyed Modem for use on the Public Switched Telephone Network"

import time
import math
import array
import board
from audiocore import RawSample
import audiopwmio

class TTYTransmitter:
    def __init__(self, output_pin):
        # constants for sine wave generation
        SIN_LENGTH = 100  # more is less choppy
        SIN_AMPLITUDE = 2 ** 12  # 0 (min) to 32768 (max)  8192 is nice
        SIN_OFFSET = 32767.5  # for 16bit range, (2**16 - 1) / 2
        DELTA_PI = 2 * math.pi / SIN_LENGTH  # happy little constant

        sine_wave = [
            int(SIN_OFFSET + SIN_AMPLITUDE * math.sin(DELTA_PI * i)) for i in range(SIN_LENGTH)
        ]
        self.tones = (
            RawSample(array.array("H", sine_wave), sample_rate=1800 * SIN_LENGTH),  # Bit 0
            RawSample(array.array("H", sine_wave), sample_rate=1400 * SIN_LENGTH),  # Bit 1
        )

        self.bit_0 = self.tones[0]
        self.bit_1 = self.tones[1]
        self.carrier = self.tones[1]


        self.char_pause = 0.1  # pause time between chars, set to 0 for fastest rate possible

        self.dac = audiopwmio.PWMAudioOut(
            output_pin
        )  # the CLUE edge connector marked "#0" to STEMMA speaker
        # The CLUE's on-board speaker works OK, not great, just crank amplitude to full before trying.
        # dac = audiopwmio.PWMAudioOut(board.SPEAKER)


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
            "LTRS",
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
            "LTRS",
        )

        self.char_count = 0
        self.current_mode = self.LTRS

        #  The 5-bit Baudot text telephone (TTY) mode is a Frequency Shift Keyed modem
        #  for use on the Public Switched Telephone network.
        #
        #   Definitions:
        #       Carrier tone is a 1400Hz tone.
        #       Binary 0 is an 1800Hz tone.
        #       Binary 1 is a 1400Hz tone.
        #       Bit duration is 20ms.

        #       Two modes exist: Letters, aka LTRS, for alphabet characters
        #       and Figures aka FIGS for numbers and symbols. These modes are switched by
        #       sending the appropriate 5-bit LTRS or FIGS character.
        #
        #   Character transmission sequence:
        #       Carrier tone transmits for 150ms before each character.
        #       Start bit is a binary 0 (sounded for one bit duration of 20ms).
        #       5-bit character code can be a combination of binary 0s and binary 1s.
        #       Stop bit is a binary 1 with a minimum duration of 1-1/2 bits (30ms)
        #
        #


    def baudot_bit(self, pitch, duration=0.022):  # spec says 20ms, but adjusted as needed
        self.dac.play(pitch, loop=True)
        time.sleep(duration)
        # dac.stop()


    def baudot_carrier(self, duration=0.15):  # Carrier tone is transmitted for 150 ms before the
        # first character is transmitted
        self.baudot_bit(self.carrier, duration)
        self.dac.stop()


    def baudot_start(self):
        self.baudot_bit(self.bit_0)


    def baudot_stop(self):
        self.baudot_bit(self.bit_1, 0.04)  # minimum duration is 30ms
        self.dac.stop()


    def send_character(self, value):
        self.baudot_carrier()  # send carrier tone
        self.baudot_start()  # send start bit tone
        for i in range(5):  # send each bit of the character
            bit = (value >> i) & 0x01  # bit shift and bit mask to get value of each bit
            self.baudot_bit(self.tones[bit])  # send each bit, either 0 or 1, of a character
        self.baudot_stop()  # send stop bit
        self.baudot_carrier()  # not to spec, but works better to extend carrier


    def send_message(self, text):
        
        for char in text:
            if char not in self.LTRS and char not in self.FIGS:  # just skip unknown characters
                # print("Unknown character:", char)
                continue

            if char not in self.current_mode:  # switch mode
                if self.current_mode == self.LTRS:
                    # print("Switching mode to FIGS")
                    self.current_mode = self.FIGS
                    self.send_character(self.current_mode.index("FIGS"))
                elif self.current_mode == self.FIGS:
                    # print("Switching mode to LTRS")
                    self.current_mode = self.LTRS
                    self.send_character(self.current_mode.index("LTRS"))
            # Send char mode at beginning of message and every 72 characters
            if self.char_count >= 72 or self.char_count == 0:
                # print("Resending mode")
                if self.current_mode == self.LTRS:
                    self.send_character(self.current_mode.index("LTRS"))
                elif self.current_mode == self.FIGS:
                    self.send_character(self.current_mode.index("FIGS"))
                # reset counter
                self.char_count = 0
            print(char)
            self.send_character(self.current_mode.index(char))
            time.sleep(self.char_pause)
            # increment counter
            self.char_count += 1

