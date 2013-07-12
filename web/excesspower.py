
import bottle
from shared import excesspower
from web.utils import *

@bottle.get('/excesspower')
@bottle.view('excesspower.html')
def index():
    return {}

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
#@succeed_or_fail
def get_channel(subsystem, channel):
    channel = _load_channel(subsystem, channel)
    with excesspower.read_h5() as h5:
        bursts = excesspower.get_bursts_table(channel).attach(h5)
        num_bursts = len(bursts)
        last_update = int(bursts.attrs['latest_output_time'])
    return {'channel': channel.todict(), 
            'num_bursts': num_bursts, 
            'last_update': last_update}

def _load_channels():
    with excesspower.read_h5() as h5:
        return excesspower.get_all_channels_from_table(h5)

def _load_channel(subsystem, name):
    with excesspower.read_h5() as h5:
        return excesspower.get_channel_from_table(h5, subsystem, name)
