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


testfile = "test/realhardware.wav"

outdata = []
byte_seq = []

with wave.open(testfile) as audioFile:
    sample_rate = audioFile.getframerate()
    chunk_size = sample_rate // 100 # 10ms chunks?
    print(sample_rate, chunk_size)
    current_chunk = 0
    
    while current_chunk * chunk_size < audioFile.getnframes():
        current_chunk += 1 # don't get stuck in a loop :)
        chunk_goertzel = goertzel(audioFile.readframes(chunk_size), sample_rate, (1300,1500), (1700,1900))
        freq_list = chunk_goertzel[0]
        power_list = []
        for i in chunk_goertzel[1]:
            power_list.append(i[2])
        top_power = max(power_list)
        dominant = -1
        if top_power > 1000000:
            dominant = freq_list[power_list.index(max(power_list))]
        if 1450 > dominant > 1351:
            byte_seq.append(0)
            print(dominant, current_chunk)
        elif dominant > 1750:
            byte_seq.append(1)
            print(dominant, current_chunk)









    