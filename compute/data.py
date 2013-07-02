
import os
import time
from pylal import frutils
from glue.gpstime import GpsSecondsFromPyUTC

_caches = {}
def get_cache(frametype):
    try:
        return _caches[frametype]
    except KeyError:
        cache = frutils.AutoqueryingFrameCache(frametype=frametype, 
                                               scratchdir="/usr1/chase.kernan")
        _caches[frametype] = cache
        return cache

def utc_to_gps_time(utc):
    return GpsSecondsFromPyUTC(utc)

def now_as_gps_time():
    return utc_to_gps_time(time.time())