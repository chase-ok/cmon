
import os
from ConfigParser import SafeConfigParser
from shared.utils import get_directories

class _TreeNode(object):
    children = []
    def print_tree(self, level=0, limit=10):
        print "  "*level + str(self)

        for child, _ in zip(self.children, range(limit)):
            child.print_tree(level=level+1)

        if len(self.children) > limit:
            print "  "*(level+1) + "..."


class _TreeLeaf(_TreeNode):
    def print_tree(self, level=0):
        print "  "*level + str(self)


class Pipeline(_TreeNode):

    def __init__(self, path):
        self.path = path
        self.ifos = []
        self.children = self.ifos

    def parse(self, stop_on=[]):
        for name in get_directories(self.path):
            self.add_ifo(name)
        if IFO not in stop_on:
            for ifo in self.ifos:
                ifo.parse(stop_on=stop_on)

    def add_ifo(self, name):
        ifo = IFO(self, name)
        self.ifos.append(ifo)
        return ifo

    def __str__(self):
        return "Pipeline [root={0.path}, #ifos={1}]"\
               .format(self, len(self.ifos))


class IFO(_TreeNode):

    def __init__(self, pipeline, name):
        self.pipeline = pipeline
        self.name = name
        self.subsystems = []
        self.children = self.subsystems

    def parse(self, stop_on=[]):
        for name in get_directories(self.path):
            self.add_subsystem(name)
        if Subsystem not in stop_on:
            for sub in self.subsystems:
                sub.parse(stop_on=stop_on)

    @property
    def path(self):
        return os.path.join(self.pipeline.path, self.name)

    def add_subsystem(self, name):
        sub = Subsystem(self, name)
        self.subsystems.append(sub)
        return sub

    def __str__(self):
        return "IFO {0.name} [#subsystems={1}]"\
               .format(self, len(self.subsystems))


class Subsystem(_TreeNode):

    def __init__(self, ifo, name):
        self.ifo = ifo
        self.name = name
        self.channels = []
        self.children = self.channels

    def parse(self, stop_on=[]):
        ini_files = [f for f in os.listdir(self.path) 
                     if f.endswith('channels.ini')]
        if not ini_files: return
        print ini_files
        #assert len(ini_files) == 1

        ini_parser = SafeConfigParser()
        ini_parser.read(os.path.join(self.path, ini_files[0]))

        for channel_name in ini_parser.sections():
            bit_width = ini_parser.getint(channel_name, "bit_width")
            sampling = ini_parser.getint(channel_name, "sample_rate")
            self.add_channel(channel_name, 
                             bit_width=bit_width, 
                             sampling=sampling)

        if Channel not in stop_on:
            for channel in self.channels:
                channel.parse(stop_on=stop_on)

    @property
    def path(self):
        return os.path.join(self.ifo.path, self.name)

    def add_channel(self, name, **kwargs):
        channel = Channel(self, name, **kwargs)
        self.channels.append(channel)
        return channel

    def __str__(self):
        return "Subsystem {0.name} [#channels={1}]"\
               .format(self, len(self.channels))


class Channel(_TreeNode):

    def __init__(self, subsystem, name, bit_width=32, sampling=1024):
        self.subsystem = subsystem
        self.name = name
        self.bit_width = bit_width
        self.sampling = sampling

        self.spectra = []
        self.triggers = []

    @property
    def children(self):
        return self.triggers + self.spectra

    def parse(self, stop_on=[]):
        if not os.path.exists(self.path):
            return

        for name in os.listdir(self.spectra_path):
            if not name.endswith(".xml"): continue

            #path formated like ..._PSD_{TIME}.xml
            time = int(name.split("_")[-1].split(".")[0])
            self.add_spectrum(time)

        for name in os.listdir(self.triggers_path):
            if not name.endswith(".xml"): continue

            #path formated like ..._triggers_{TIME}_{DURATION}.xml
            parts = name.split("_")
            time = int(parts[-2])
            duration = int(parts[-1].split(".")[0])
            self.add_trigger(time, duration)

        if Spectrum not in stop_on:
            for spectrum in self.spectra:
                spectrum.parse(stop_on=stop_on)
        if Trigger not in stop_on:
            for trigger in self.triggers:
                trigger.parse(stop_on=stop_on)

    def add_spectrum(self, time):
        spectrum = Spectrum(self, time)
        self.spectra.append(spectrum)
        return spectrum

    def add_trigger(self, time, duration):
        trigger = Trigger(self, time, duration)
        self.triggers.append(trigger)
        return trigger

    @property
    def path(self):
        return os.path.join(self.subsystem.path, self.name)

    @property
    def spectra_path(self):
        return os.path.join(self.path, "spectra")

    @property
    def triggers_path(self):
        return os.path.join(self.path, "triggers")

    def __str__(self):
        return "Channel {0.name} [sampling={0.sampling}, bit_width={0.bit_width}, #spectra={1}, #triggers={2}]"\
               .format(self, len(self.children), len(self.triggers))


class Spectrum(_TreeLeaf):

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

class Trigger(_TreeLeaf):

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
    #pipe = Pipeline("/home/detchar/excesspower")
    #pipe.parse(stop_on=[Spectrum, Trigger])
    #pipe.print_tree()

    #s1 = pipe.ifos[0].subsystems[0].channels[0].spectra[0]
    #print s1, s1.path
    #s1.parse()

    from glue.ligolw import table
    from glue.ligolw import lsctables
    from glue.ligolw import utils

    xml_doc = utils.load_filename("/home/detchar/excesspower/H1/PEM/PEM-CS_ACC_BEAMTUBE_YMAN_Z_DQ/spectra/H1-PEM_CS_ACC_BEAMTUBE_YMAN_Z_DQ_PSD_excesspower-1045941856-40.xml.gz", gz=True)
    print xml_doc