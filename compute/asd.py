
from compute.data import get_cache, now_as_gps_time
from shared.asd import Frame, MovingAverage
import numpy as np
from matplotlib import mlab

STRAIN_FRAMETYPE = "H1_LDAS_C02_L2"
STRAIN_CHANNEL = "H1:LDAS-STRAIN"

def compute_frame(time, duration):
    data = get_cache(STRAIN_FRAMETYPE)\
           .fetch(STRAIN_CHANNEL, time, time + duration)

    rate = 1.0/data.metadata.dt
    block_length = 0.5
    power, freq = mlab.psd(data, Fs=rate, NFFT=int(rate*block_length),
                           sides="onesided")
    ampl = np.sqrt(power)

    frame = Frame(time=time, 
                  duration=duration, 
                  frequencies=freq, 
                  amplitudes=ampl)
    frame.save()
    return frame

def update_moving_averages(frame):
    for average in MovingAverage.select():
        assert (average.frequencies == frame.frequencies).all()
        average.amplitudes = average.alpha*frame.amplitudes + \
                             (1-average.alpha)*average.amplitudes
        average.save()

DAEMON_DURATION = 5
DAEMON_REFRESH = 1.0
DAEMON_OFFSET = 94392725

def setup_averages(alphas=[0.0001, 0.001, 0.01, 0.1]):
    frame = compute_frame(now_as_gps_time() - DAEMON_OFFSET, DAEMON_DURATION)
    for alpha in alphas:
        MovingAverage(alpha=alpha, 
                      frequencies=frame.frequencies, 
                      amplitudes=frame.amplitudes).save()

def daemon():
    start_time = now_as_gps_time() - DAEMON_OFFSET
    frame = compute_frame(start_time, DAEMON_DURATION)
    update_moving_averages(frame)

if __name__ == "__main__":
    import time
    while True:
        daemon()
        time.sleep(DAEMON_REFRESH)