# Trying to redo the reading stuff using a different algorithm, that should hopefully allow for real-time decoding?

import math
import wave
from time import monotonic_ns

def goertzel(samples, sample_rate, *freqs):
    """
    Implementation of the Goertzel algorithm, useful for calculating individual
    terms of a discrete Fourier transform.
    `samples` is a windowed one-dimensional signal originally sampled at `sample_rate`.
    The function returns 2 arrays, one containing the actual frequencies calculated,
    the second the coefficients `(real part, imag part, power)` for each of those frequencies.
    For simple spectral analysis, the power is usually enough.
    Example of usage :
        
        freqs, results = goertzel(some_samples, 44100, (400, 500), (1000, 1100))
    """
    window_size = len(samples)
    f_step = sample_rate / float(window_size)
    f_step_normalized = 1.0 / window_size

    # Calculate all the DFT bins we have to compute to include frequencies
    # in `freqs`.
    bins = set()
    for f_range in freqs:
        f_start, f_end = f_range
        k_start = int(math.floor(f_start / f_step))
        k_end = int(math.ceil(f_end / f_step))

        if k_end > window_size - 1: raise ValueError('frequency out of range %s' % k_end)
        bins = bins.union(range(k_start, k_end))

    # For all the bins, calculate the DFT term
    n_range = range(0, window_size)
    freqs = []
    results = []
    for k in bins:

        # Bin frequency and coefficients for the computation
        f = k * f_step_normalized
        w_real = 2.0 * math.cos(2.0 * math.pi * f)
        w_imag = math.sin(2.0 * math.pi * f)

        # Doing the calculation on the whole sample
        d1, d2 = 0.0, 0.0
        for n in n_range:
            y  = samples[n] + w_real * d1 - d2
            d2, d1 = d1, y

        # Storing results `(real part, imag part, power)`
        results.append((
            0.5 * w_real * d1 - d2, w_imag * d1,
            d2**2 + d1**2 - w_real * d1 * d2)
        )
        freqs.append(f * sample_rate)
    return freqs, results

class Decoder:
    def __init__(self, baudrate = 45):
        self.baudrate = baudrate
    
    def decode_from_file(self, file):
        # get samples from the file
        with wave.open(file) as audiofile:
            pass
        




# testing below
import wave
import time

testfile = "wav/tones/1400.wav"

with wave.open(testfile) as audioFile:
    
    data = []
    sample_rate = audioFile.getframerate()
    for i in range(audioFile.getnframes()):
        data.append(int.from_bytes(audioFile.readframes(1), "little", signed = True))
    print("starting goertzel...")
    starttime = time.monotonic_ns()
    outdata = goertzel(data, sample_rate, (1350,1450), (1750,1850))
    gtime = time.monotonic_ns() - starttime
    print("saving......")
    with open("fart.txt", "w") as fartfile:
        for i in range(len(outdata[0])):
            fartfile.write(str(outdata[0][i]))
            fartfile.write("\t")
            fartfile.write(str(outdata[1][i][2]))
            fartfile.write("\n")
    print("done in ", gtime // 1000000, "ms")