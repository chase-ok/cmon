
import os
import time
from pylal import frutils
from glue.gpstime import GpsSecondsFromPyUTC

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

def utc_to_gps_time(utc):
    return GpsSecondsFromPyUTC(utc)

OFFSET = 94346325
def now_as_gps_time(offset=OFFSET):
    return utc_to_gps_time(time.time()) - OFFSET