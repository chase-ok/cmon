
from shared import data
from shared.utils import memoized

IFO = "H1"
EXCESS_POWER_ROOT = "/home/detchar/excesspower/ER3/{0}".format(IFO)

H5_FILE = "excesspower.h5"
write_h5 = lambda: data.write_h5(H5_FILE)
read_h5 = lambda: data.read_h5(H5_FILE)

MAX_CHANNEL_NAME_LENGTH = 64
MAX_SUBSYSTEM_NAME_LENGTH = 8
MAX_DIRECTORY_LENGTH = 256 + MAX_CHANNEL_NAME_LENGTH + MAX_SUBSYSTEM_NAME_LENGTH

channels_table = data.GenericTable('channels', 
        dtype=[('subsystem', str, MAX_SUBSYSTEM_NAME_LENGTH),
               ('name', str, MAX_CHANNEL_NAME_LENGTH),
               ('directory', str, MAX_DIRECTORY_LENGTH)],
        chunk_size=1)

def get_all_channels_from_table(h5):
    table = channels_table.attach(h5)
    return [Channel(**fields) for fields in table.iterdict()]

def get_channel_from_table(h5, subsystem, name):
    for fields in channels_table.attach(h5).iterdict():
        if fields['subsystem'] == subsystem and fields['name'] == name:
            return Channel(**fields)
    raise ValueError('No such channel')

class Channel(object):

    def __init__(self, subsystem='', name='', directory=''):
        self.subsystem = subsystem
        self.name = name
        self.directory = directory

    def todict(self):
        return {'subsystem': self.subsystem, 
                'name': self.name, 
                'directory': self.directory}

    @property
    def h5_path(self):
        return "{0.subsystem}/{0.name}".format(self)

    def __repr__(self):
        return "Channel(name='{0.name}', subsystem='{0.subsystem}', directory='{0.directory}')"\
               .format(self)

    def __str__(self):
        return "Channel {0.name} [subsystem={0.subsystem}, directory={0.directory}]"\
               .format(self)


burst_column_names = ["peak_time", "peak_time_ns", 
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
            for name in burst_column_names]

def get_bursts_table(channel):
    return data.GenericTable("{0.h5_path}/bursts".format(channel),
                             dtype=_make_burst_dtype())

class Output(object):        

    def __init__(self, channel=None, time=-1, duration=-1, path=''):
        self.channel = channel
        self.time = time
        self.duration = duration
        self.path = path
        self.bursts = None

    def __repr__(self):
        return "Output(channel='{0.channel.name}', time={0.time}, duration={0.duration}, path='{0.path}')"\
               .format(self)

    def __str__(self):
        return "Output channel={0.channel.name}, time={0.time}, duration={0.duration}"\
               .format(self)

