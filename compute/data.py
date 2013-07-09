
from shared.utils import memoized
from pylal import frutils, seriesutils
from lal import LIGOTimeGPS


@memoized
def get_cache(frametype):
    return frutils.AutoqueryingFrameCache(frametype=frametype,
                                          scratchdir="/usr1/chase.kernan")


def read_series(channel, time, duration):
    data = get_cache(channel.type)\
           .fetch(channel.full_name, time, time + duration)
    return seriesutils.fromarray(data,
                                 epoch=LIGOTimeGPS(time),
                                 deltaT=data.metadata.dt)
