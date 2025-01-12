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
        self.noise_floor = 250 #(???)
    
    def decode_from_file(self, file):
        # get samples from the file
        samplerate = 0
        samples_per_ms = 0 # how many samples in 1ms? idk if i need this, but we'll see
        with wave.open(file) as audiofile:
            samplerate = audiofile.getframerate()
            samples_per_ms = samplerate / 1000 
            return 
        




# testing below
import wave
import time

testfile = "test/test.wav"

outdata = []

with wave.open(testfile) as audioFile:
    freqlist = []
    data = []
    sample_rate = audioFile.getframerate()
    samps_per_ms = sample_rate // 1000
    read_frame = 0
    #while read_frame < audioFile.getnframes():
    read_frame += samps_per_ms * 10
    samples = audioFile.readframes(samps_per_ms * 100) # 10ms of data
    smalld = []
    for i in samples:
        smalld.append(i)
    outdata = goertzel(smalld, sample_rate, (1300,1500), (1750, 1850))

    