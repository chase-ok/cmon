
from pylal.dq.dqFrameUtils import Channel

strain = Channel("H1:LDAS-STRAIN", "H1_LDAS_C02_L2", sampling=16384)

def delta_t(channel): return 1.0/channel.sampling
def full_name(channel): return channel.ifo + ":" + channel.name