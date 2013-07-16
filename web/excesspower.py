
import bottle
from shared import excesspower
from shared.utils import now_as_gps_time
from web.utils import *
import numpy as np

@bottle.get('/excesspower')
def index():
    bottle.redirect("/excesspower/FAKE/STRAIN")

@bottle.get('/excesspower/ifo')
@succeed_or_fail
def get_ifo():
    return {'ifo': excesspower.IFO}

@bottle.get('/excesspower/channels')
@succeed_or_fail
def get_channels():
    channels = _load_channels()
    return {'channels': [channel.todict() for channel in channels]}

@bottle.get('/excesspower/subsystems')
@succeed_or_fail
def get_subsystems():
    subsystems = set(channel.subsystem for channel in _load_channels())
    return {'subsystems': list(subsystems)}

@bottle.get('/excesspower/<subsystem>')
@succeed_or_fail
def get_subsystem(subsystem):
    channels = [channel.todict() for channel in _load_channels()
                if channel.subsystem == subsystem]
    if channels:
        return {'channels': channels}
    else:
        raise ValueError("No such subsystem")

@bottle.get('/excesspower/<subsystem>/<channel>')
@bottle.view("excesspower.html")
def get_channel(subsystem, channel):
    try:
        _load_channel(subsystem, channel)
    except:
        bottle.abort(404, "No such channel.")

    return {'root': WEB_ROOT,
            'ifo': excesspower.IFO,
            'subsystem': subsystem,
            'channel': channel,
            'startTime': float(now_as_gps_time())}

@bottle.get('/excesspower/<subsystem>/<channel>/summary')
@succeed_or_fail
def get_channel_summary(subsystem, channel):
    channel = _load_channel(subsystem, channel)
    with excesspower.read_h5() as h5:
        bursts = excesspower.get_bursts_table(channel).attach(h5)
        num_bursts = len(bursts)
        last_update = int(bursts.attrs['latest_output_time'])
    return {'channel': channel.todict(), 
            'num_bursts': num_bursts, 
            'last_update': last_update}

@bottle.get('/excesspower/<subsystem>/<channel>/bursts_since/<time:int>')
@succeed_or_fail
def get_bursts_since(subsystem, channel, time):
    limit = bottle.request.query.limit or 100
    channel = _load_channel(subsystem, channel)

    with excesspower.read_h5() as h5:
        table = excesspower.get_bursts_table(channel).attach(h5)
        bursts = excesspower.get_bursts_since(table, time, limit=int(limit))

    return {'bursts': map(_convert_numpy_dict, bursts)}

@bottle.get('/excesspower/<subsystem>/<channel>/bursts/<start_time:int>-<end_time:int>')
@succeed_or_fail
def get_bursts_since(subsystem, channel, start_time, end_time):
    limit = bottle.request.query.limit or 100
    channel = _load_channel(subsystem, channel)

    with excesspower.read_h5() as h5:
        table = excesspower.get_bursts_table(channel).attach(h5)
        bursts = excesspower.get_bursts_in_time_range(table, 
                 start_time, end_time, limit=int(limit))

    return {'bursts': map(_convert_numpy_dict, bursts)}


def _load_channels():
    with excesspower.read_h5() as h5:
        return excesspower.get_all_channels_from_table(h5)

def _load_channel(subsystem, name):
    with excesspower.read_h5() as h5:
        return excesspower.get_channel_from_table(h5, subsystem, name)

def _convert_numpy_dict(d):
    return dict((k, np.asscalar(v)) for k, v in d.iteritems())
