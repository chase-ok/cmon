
import utils

STRAIN_FRAMETYPE = "H1_LDAS_C02_L2"
STRAIN_CHANNEL = "H1:LDAS-STRAIN"

def compute_asd(start_time, duration):
    from data import get_cache
    import numpy as np
    from matplotlib import mlab

    data = get_cache(STRAIN_FRAMETYPE)\
           .fetch(STRAIN_CHANNEL, start_time, duration)

    rate = 1.0/data.metadata.dt
    block_length = 0.5
    power, freq = mlab.psd(data, Fs=rate, NFFT=int(rate*block_length),
                           sides="onesided")
    return freq, np.sqrt(power)

DAEMON_FILE = "{0}/asd.npz".format(utils.DATA)
DAEMON_DURATION = 60
DAEMON_REFRESH = 10
DAEMON_OFFSET = 94392725

def daemon():
    start_time = utils.now_as_gps_time() - DAEMON_OFFSET
    freq, ampl = compute_asd(start_time, start_time + DAEMON_DURATION)

    import os
    try:
        os.remove(DAEMON_FILE)
    except OSError:
        pass

    import numpy as np
    np.savez(DAEMON_FILE,
             time=np.array(start_time),
             frequency=freq,
             amplitude=ampl)

def read_from_daemon(native_python=False):
    import numpy as np
    
    data = np.load(DAEMON_FILE)
    if native_python:
        return {'time': float(data['time']),
                'frequency': data['frequency'].tolist(),
                'amplitude': data['amplitude'].tolist()}
    else:
        return data

if __name__ == "__main__":
    #import os; os.makedirs(DAEMON_DIR)
    utils.make_daemon_loop("asd", daemon, 
                           sleep=DAEMON_REFRESH)
