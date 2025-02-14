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
    took = time.ticks_diff(end_time, time.ticks_us())
    samp_num = len(samples)
    print(str(samp_num) + " samples collected, " + str(took) + " us over estimate")
    return samples


def get_data_on_samples(sample_list:list):
    zero_point = 32768
    noise_floor = 100
    zero_counts = 0
    above_zero = True
    for s in sample_list:
        if s > zero_point + noise_floor and above_zero:
            zero_counts += 1
            above_zero = False
        elif s < zero_point - noise_floor and not above_zero:
            zero_counts += 1
            above_zero = True
    print("Counted " + str(zero_counts) + " crossings from " + str(len(sample_list)) + " samples.")

    if zero_counts < 14: 
        print("Less than 1400 Hz???")
    elif zero_counts < 16:
        print("Should be 1400Hz (Mark)")
    elif zero_counts < 20:
        print("Should be 1800Hz (Space)")
    else:
        print("More than 20 crossings, noise floor too low???")