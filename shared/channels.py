
# Turns out we can't use pylal inside of a CGI script...
#from pylal.dq.dqFrameUtils import Channel

class Channel(object):

    def __init__(self, full_name, type, sampling):
        self.full_name = full_name
        self.ifo, self.name = full_name.split(":")
        self.type = type
        self.sampling = sampling

    @property
    def dt(self):
        return 1.0/self.sampling

    def __str__(self):
        return "Channel {0.full_name} type={0.type} sampling{0.sampling}"\
               .format(self)

strain = Channel("H1:LDAS-STRAIN", "H1_LDAS_C02_L2", 16384)