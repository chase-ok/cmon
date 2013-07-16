
from shared import data, channels
from shared.utils import memoized
from os.path import join
import bisect

EXCESS_POWER_ROOT = "/home/detchar/excesspower"
ER3_TRIGGERS_ROOT = join(EXCESS_POWER_ROOT, "ER3")
ER4_TRIGGERS_ROOT = join(EXCESS_POWER_ROOT, "ER4")
TRIGGERS_ROOT = ER3_TRIGGERS_ROOT
SPECTRA_ROOT = EXCESS_POWER_ROOT

H5_FILE = "excesspower.h5"
write_h5 = lambda: data.write_h5(H5_FILE)
read_h5 = lambda: data.read_h5(H5_FILE)

def add_channel(ifo, subsystem, name):
    channel = channels.Channel(ifo=ifo, subsystem=subsystem, name=name)
    channel.properties['excess_power'] = True
    channels.add_channel(channel)
    
def get_all_channels():
    return [channel for channel in channels.get_all_channels()
            if channel.properties.get('excess_power')]

def get_trigger_directory(channel):
    if channel.subsystem == 'FAKE':
        path_format = '{0.ifo}/FAKE_{0.name}_excesspower'
    else:
        path_format = '{0.ifo}/{0.subsystem}-{0.name}_excesspower'
    return join(TRIGGERS_ROOT, path_format.format(channel))
    
def get_spectrum_directory(channel):
    return JOIN(SPECTRA_ROOT, 
                '{0.ifo}/{0.subsystem}/{0.name}/spectra'.format(channel)) 


BURST_COLUMN_NAMES = ["peak_time", "peak_time_ns", 
                      "start_time", "start_time_ns",
                      "duration",
                      "central_freq", "bandwidth",
                      "amplitude", "snr", "confidence",
                      "chisq", "chisq_dof"]

@memoized
def _make_burst_dtype():
    from glue.ligolw import types
    from glue.ligolw.lsctables import SnglBurstTable
    return [(name, types.ToNumPyType[SnglBurstTable.validcolumns[name]])
            for name in BURST_COLUMN_NAMES]

def get_bursts_table(channel):
    return data.GenericTable("{0.h5_path}/bursts".format(channel),
                             dtype=_make_burst_dtype())

def get_bursts_since(bursts_table, time, limit=100):
    length = len(bursts_table)
    bursts = []
    for i in range(limit):
        burst = bursts_table.read_dict(length-(i+1))
        if burst['start_time'] < time: break
        bursts.append(burst)
    return reversed(bursts)

def time_to_burst_index(bursts_table, time, low=0, high=None):
    if low < 0: raise ValueError('low must be non-negative')
    if high is None: high = len(bursts_table)
    while low < high:
        mid = (low + high)//2
        if bursts_table[mid].start_time < time: low = mid + 1
        else: high = mid
    return low

def get_bursts_in_time_range(bursts_table, low, high, limit=100):
    if low >= high: raise ValueError('high must be greater than low')
    low_index = time_to_burst_index(bursts_table, low)
    max_high = min(len(bursts_table), low_index + limit)
    high_index = time_to_burst_index(bursts_table, high,
                                     low=low_index, high=max_high)
    return [bursts_table.read_dict(i) for i in xrange(low_index, high_index)]


class TriggerFile(object):        

    def __init__(self, channel=None, time=-1, duration=-1, path=''):
        self.channel = channel
        self.time = time
        self.duration = duration
        self.path = path

    def __repr__(self):
        return """TriggerFile(channel='{0.channel.name}', 
                              time={0.time}, 
                              duration={0.duration}, 
                              path='{0.path}')"""\
               .replace(' ', '').replace('\n', ' ').format(self)

    def __str__(self):
        return """Triggers channel={0.channel.name}, 
                           time={0.time}, 
                           duration={0.duration}"""\
               .replace(' ', '').replace('\n', ' ').format(self)

