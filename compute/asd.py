
from compute.data import read_series
from shared.utils import now_as_gps_time
from shared.asd import open_h5
from pylal.seriesutils import compute_average_spectrum
import numpy as np


def compute_asd(table, time, duration):
    series = read_series(table.channel, time, duration)
    spectrum = compute_average_spectrum(series, table.seglen, table.stride,
                                        average="median")

    amplitudes = np.sqrt(spectrum.data.data)
    with open_h5(mode="w") as h5:
        table.attach(h5).append(time, amplitudes)
    return amplitudes


def test():
    import shared.asd
    compute_asd(shared.asd.strain_asd, now_as_gps_time(), 100)
    with open_h5("r") as h5:
        table = shared.asd.strain_asd.attach(h5)
        time, amplitudes = table.latest
        print time, table.frequencies[...], amplitudes


def update_moving_averages(frame):
    for average in MovingAverage.select():
        assert (average.frequencies == frame.frequencies).all()
        average.amplitudes = average.alpha*frame.amplitudes + \
                             (1-average.alpha)*average.amplitudes
        average.save()


DAEMON_DURATION = 5
DAEMON_REFRESH = 1.0


def setup_averages(alphas=[0.0001, 0.001, 0.01, 0.1]):
    frame = compute_frame(now_as_gps_time() - DAEMON_OFFSET, DAEMON_DURATION)
    for alpha in alphas:
        MovingAverage(alpha=alpha,
                      frequencies=frame.frequencies,
                      amplitudes=frame.amplitudes).save()


def daemon():
    frame = compute_frame(now_as_gps_time(), DAEMON_DURATION)
    frame.save()
    update_moving_averages(frame)


if __name__ == "__main__":
    test()
    #import time
    #while True:
    #    daemon()
    #    time.sleep(DAEMON_REFRESH)
