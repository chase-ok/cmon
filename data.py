
import os    
#os.environ['LIGO_DATAFIND_SERVER'] = "ldr.ligo.caltech.edu"
#os.environ['X509_USER_PROXY'] = "/home/chase.kernan/public_html/cgi-bin/cmon/x509up_p7702.filexuRlR5.1"

from pylal import frutils

_caches = {}
def get_cache(frametype):
    try:
        return _caches[frametype]
    except KeyError:
        cache = frutils.AutoqueryingFrameCache(frametype=frametype, 
                                               scratchdir="/tmp")
        _caches[frametype] = cache
        return cache
