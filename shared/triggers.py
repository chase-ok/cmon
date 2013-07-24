

from shared import data, channels
from shared.utils import memoized
from os.path import join
import bisect
from collections import namedtuple
import numpy as np


H5_FILE_TEMPLATE = "triggers-{0.file_path}.h5"


Source = namedtuple('Source', 'name root')
_sources = set()
def add_source(source):
    _sources.add(source)

def find_source(name):
    for source in _sources:
        if source.name == name:
            return source
    return None

_PROPERTY_TEMPLATE = 'trigger_source_{0.name}'

def add_channel(source, ifo, subsystem, name):
    channel = channels.Channel(ifo=ifo, subsystem=subsystem, name=name)
    channel.properties[_PROPERTY_TEMPLATE.format(source)] = True
    channels.add_channel(channel)
    return channel

def has_source(channel, source):
    return channel.properties.get(_PROPERTY_TEMPLATE.format(source), False)
    
def set_not_source(channel, source, h5=None):
    channel.properties[_PROPERTY_TEMPLATE.format(source)] = False
    channel.flush_properties(h5=h5)

def get_all_channels(source):
    return [channel for channel in channels.get_all_channels()
            if has_source(channel, source)]


def get_trigger_directory(source, channel):
    if channel.subsystem == 'FAKE':
        path_format = '{0.ifo}/FAKE_{0.name}_{1}'
    else:
        path_format = '{0.ifo}/{0.subsystem}-{0.name}_{1}'
    return join(source.root, path_format.format(channel, source.name))


File = namedtuple('File', 'source channel time duration path')


COLUMN_NAMES = ["peak_time", "peak_time_ns", 
                "start_time", "start_time_ns",
                "duration",
                "central_freq", "bandwidth",
                "amplitude", "snr"] # , "confidence"

@memoized
def _make_dtype():
    from glue.ligolw import types
    from glue.ligolw.lsctables import SnglBurstTable
    return [(name, types.ToNumPyType[SnglBurstTable.validcolumns[name]])
            for name in COLUMN_NAMES]


def get_h5_file(channel):
    return H5_FILE_TEMPLATE.format(channel)

@memoized
def get_table(source):
    assert source in _sources
     # 1000 rows = 54 kb chunks, good size
    return data.GenericTable(source.name, dtype=_make_dtype(), chunk_size=1000,
                             initial_size=2**18)

def describe_table(table):
    return { 'num_triggers': len(table),
             'start_time': table[0].start_time,
             'end_time': table[-1].start_time,
             'last_updated': get_last_updated(table),
             'source': table.meta.name }


def get_last_updated(table):
    return table.attrs.get('last_updated', 0)

def set_last_updated(table, last_updated):
    table.attrs['last_updated'] = last_updated


def get_triggers_since(table, time, limit=100):
    length = len(table)
    trigger = []
    for i in range(limit):
        trigger = table.read_dict(length-(i+1))
        if trigger['start_time'] < time: break
        trigger.append(trigger)
    return reversed(trigger)


def time_to_trigger_index(table, time, low=0, high=None):
    if low < 0: raise ValueError('low must be non-negative')
    if high is None: high = len(table)
    while low < high:
        mid = (low + high)//2
        if table[mid].start_time < time: low = mid + 1
        else: high = mid
    return low


def get_triggers_in_time_range(table, low, high, limit=100):
    if low >= high: raise ValueError('high must be greater than low')
    low_index = time_to_trigger_index(table, low)
    max_high = min(len(table), low_index + limit)
    high_index = time_to_trigger_index(table, high,
                                       low=low_index, high=max_high)
    return [table.read_dict(i) for i in xrange(low_index, high_index)]
    

DENSITY_FREQ_BINS = np.logspace(2, 4, 8)
DENSITY_TIME_CHUNK = 1000 # secs
DENSITY_DTYPE = [('time', np.uint32), 
                 ('density', (np.float32, (DENSITY_FREQ_BINS.size,)))]

@memoized
def get_density_table(source):
    assert source in _sources
    return data.GenericTable("{0.name}_density".format(source), 
                             dtype=DENSITY_DTYPE, 
                             chunk_size=1000,
                             initial_size=2**14)

def fix_properties():
    import copy
    with data.write_h5(channels.H5_FILE) as h5:
        for channel in channels.get_all_channels(h5=h5):
            print channel
            
            if "excesspower" in channel.properties:
                del channel.properties["excesspower"]
            if "source_excesspower" in channel.properties:
                value = channel.properties["source_excesspower"]
                del channel.properties["source_excesspower"]
            else:
                value = False
            channel.properties["trigger_source_excesspower"] = value
            if "source_omicron" in channel.properties:
                value = channel.properties["source_omicron"]
                del channel.properties["source_omicron"]
            else:
                value = False
            channel.properties["trigger_source_omicron"] = value
            
            props = copy.deepcopy(channel.properties)
            channel.clear_properties(h5=h5)
            channel.properties = props
            channel.flush_properties(h5=h5)
            print channel.properties

def dumpTimes():
    fakeSource = Source("excesspower", "")
    add_source(fakeSource)
    with data.read_h5("triggers-H1-FAKE-STRAIN.h5") as h5:
        table = get_table(fakeSource).attach(h5)
        return table.dataset[:len(table), "start_time"]
