
from shared.utils import get_directories, get_files
import os
from os.path import join
import re
from ConfigParser import SafeConfigParser

IFO = "H1"
EXCESS_POWER_ROOT = "/home/detchar/excesspower/ER3/{0}".format(IFO)

_channel_re = re.compile('(?P<subsystem>[A-Z0-9]+)_(?P<channel>[_A-Z0-9]+)_excesspower\\Z')
_time_re = re.compile('(?P<ifo>[A-Z0-9]+)-(?P<subsystem>[A-Z0-9]+)_(?P<channel>[_A-Z0-9]+)_excesspower-(?P<time>[0-9]+)-(?P<duration>[0-9]+)\\.xml\\Z')

def read_channels(root=EXCESS_POWER_ROOT):
    channels = []
    for directory in get_directories(root):
        match = _channel_re.match(directory)
        if not match: continue

        channels.append(Channel(subsystem=match.group('subsystem'),
                                name=match.group('channel'),
                                directory=join(root, directory)))

    return channels

class Channel(object):

    def __init__(self, subsystem='', name='', directory=''):
        self.subsystem = subsystem
        self.name = name
        self.directory = directory

    def read_outputs(self):
        outputs = []
        for subdir in get_directories(self.directory):
            try:
                base_time = int(subdir)
                if base_time < 0: raise ValueError
            except ValueError:
                continue

            subdir_path = join(self.directory, subdir)
            for file in get_files(subdir_path):
                output = self._parse_output(subdir_path, file)
                if output: outputs.append(output)

        return outputs

    def read_latest_output(self):
        subdir = sorted(get_directories(self.directory), reverse=True)[0]
        subdir_path = join(self.directory, subdir)

        # abusing that the files are named TIME_DURATION.xml
        # if that ever changes, this method will no longer work
        for file in sorted(get_files(subdir_path), reverse=True):
            output = self._parse_output(subdir_path, file)
            if output: return output
        return None

    def _parse_output(self, subdir_path, file):
        match = _time_re.match(file)
        if not match: return None

        assert IFO == match.group('ifo')
        assert self.subsystem == match.group('subsystem')
        assert self.name == match.group('channel')

        return Output(channel=self,
                      time=int(match.group('time')),
                      duration=int(match.group('duration')),
                      path=join(subdir_path, file))

    def __repr__(self):
        return "Channel(name='{0.name}', subsystem='{0.subsystem}', directory='{0.directory}'')"\
               .format(self)

    def __str__(self):
        return "Channel {0.name} [subsystem={0.subsystem}, directory={0.directory}]"\
               .format(self)


class Output(object):

    def __init__(self, channel=None, time=-1, duration=-1, path=''):
        self.channel = channel
        self.time = time
        self.duration = duration
        self.path = path

    def read(self):
        from glue.ligolw import table
        from glue.ligolw import lsctables
        from glue.ligolw import utils

        xml_doc = utils.load_filename(self.path, gz=False)
        return xml_doc

    def __repr__(self):
        return "Output(channel='{0.channel.name}', time={0.time}, duration={0.duration}, path='{0.path}')"\
               .format(self)

    def __str__(self):
        return "Output channel={0.channel.name}, time={0.time}, duration={0.duration}"\
               .format(self)


class Spectrum(object):

    def __init__(self, channel, time):
        self.channel = channel
        self.time = time

    @property
    def path(self):
        name = "{0.channel.subsystem.ifo.name}-{0.channel.name}_PSD_{0.time}.xml"\
               .format(self)
        return os.path.join(self.channel.spectra_path, name)

    def parse(self, stop_on=[]):
        from glue.ligolw import table
        from glue.ligolw import lsctables
        from glue.ligolw import utils

        xml_doc = utils.load_filename(self.path, gz=False)
        print xml_doc

    def __str__(self):
        return "Spectrum t={0.time}".format(self)

class Trigger(object):

    def __init__(self, channel, time, duration):
        self.channel = channel
        self.time = time
        self.duration = duration

    @property
    def path(self):
        name = "{0.channel.subsystem.ifo.name}_{0.channel.name}_triggers_{0.time}_{0.duration}.xml"\
               .format(self)
        return os.path.join(self.channel.triggers_path, name)

    def parse(self, stop_on=[]):
        print "parsing trigger"

    def __str__(self):
        return "Trigger t={0.time} duration={0.duration}".format(self)

if __name__ == "__main__":
    channels = read_channels()
    channels[0].read_latest_output().read()
