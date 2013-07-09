
from shared import channels
from pylal import frutils, seriesutils
from lal import LIGOTimeGPS

STRAIN_FRAMETYPE = "H1_LDAS_C02_L2"
STRAIN_CHANNEL = "H1:LDAS-STRAIN"

_caches = {}
def get_cache(frametype):
    try:
        return _caches[frametype]
    except KeyError:
        cache = frutils.AutoqueryingFrameCache(frametype=frametype, 
                                               scratchdir="/usr1/chase.kernan")
        _caches[frametype] = cache
        return cache

def read_series(channel, time, duration):
    name = channels.full_name(channel)
    data = get_cache(channel.type).fetch(name, time, time + duration)
    return seriesutils.fromarray(data, 
                                 epoch=LIGOTimeGPS(time), 
                                 deltaT=data.metadata.dt)
