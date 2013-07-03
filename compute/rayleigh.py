
from compute.data import get_cache, now_as_gps_time, STRAIN_FRAMETYPE, STRAIN_CHANNEL
from shared.rayleigh import Frame, Block
import numpy as np
from matplotlib import mlab

def compute_rayleigh(time, stride=0.1, num_strides=10):
    duration = stride*num_strides
    data = get_cache(STRAIN_FRAMETYPE)\
           .fetch(STRAIN_CHANNEL, time, time+duration)

    rate = 1.0/data.metadata.dt
    chunk_size = int(len(data)/num_strides)

    shared_freq = None
    powers = np.empty((num_strides, chunk_size//2 + 1), np.float64)
    for i in range(num_strides):
        subset = data[i*chunk_size:(i+1)*chunk_size]
        power, freq = mlab.psd(subset, Fs=rate, NFFT=int(rate*stride))
        
        if shared_freq is None:
            shared_freq = freq
        else:
            assert (shared_freq == freq).all()
        powers[i, :] = power.T

    rs = powers.std(axis=0)/powers.mean(axis=0)
    return Frame(time=time,
                 stride=stride,
                 num_strides=num_strides,
                 frequencies=shared_freq,
                 rs=rs)

def compute_rayleigh_block(start_time, 
                           num_frames=60, 
                           stride=0.1, 
                           num_strides=10):
    frame_duration = stride*num_strides
    times = [start_time + i*frame_duration for i in range(num_frames)]
    frames = [compute_rayleigh(time, stride=stride, num_strides=num_strides)
              for time in times]

    return Block(start_time=start_time,
                 time_offsets=np.array(times)-start_time,
                 stride=stride,
                 num_strides=num_strides,
                 frequencies=frames[0].frequencies,
                 rs=np.vstack(tuple(frame.rs for frame in frames)))

def daemon():
    block = compute_rayleigh_block(now_as_gps_time())
    block.save()

if __name__ == "__main__":
    import time
    while True:
        daemon()
        print "done!"
        time.sleep(1)
