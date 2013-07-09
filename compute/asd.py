
from compute.data import read_series
from shared.asd import write_h5
from pylal.seriesutils import compute_average_spectrum
import numpy as np


def compute_asd(table, time, duration):
    series = read_series(table.channel, time, duration)
    spectrum = compute_average_spectrum(series, table.seglen, table.stride,
                                        average="median")

    amplitudes = np.sqrt(spectrum.data.data)
    with write_h5() as h5:
        table.attach(h5).append(time, amplitudes)
    return amplitudes


def compute_latest_strain_asd(duration=5):
    from shared.asd import strain_asd
    from shared.utils import now_as_gps_time
    compute_asd(strain_asd, now_as_gps_time(), duration)


if __name__ == "__main__":
    compute_latest_strain_asd()
