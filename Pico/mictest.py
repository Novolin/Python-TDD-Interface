from machine import ADC # type:ignore
import time

# test to see if I can do it at all idfk

def read_mic():
    # reads 5ms at 100khz
    mic = ADC(26)
    samples =[]
    end_time  = time.ticks_add(time.ticks_us(), 5000)
    while time.ticks_diff(end_time, time.ticks_us()) > 0:
        nextsamp = time.ticks_add(time.ticks_us(), 50)
        samples.append(mic.read_u16())
        while time.ticks_diff(nextsamp, time.ticks_us()) > 0:
            pass # wait for the next sample time.
    took = time.ticks_diff(end_time, time.ticks_us())
    samp_num = len(samples)
    print(str(samp_num) + " samples collected, " + str(took) + " us over estimate")
    return samples