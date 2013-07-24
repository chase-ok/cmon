
import bottle
from shared import excesspower as ep, channels, data
from shared.utils import now_as_gps_time
from web.utils import *
import numpy as np

@bottle.get('/excesspower')
def index():
    bottle.redirect("/excesspower/H1/FAKE/STRAIN")

@bottle.get('/excesspower/channels')
@succeed_or_fail
def get_channels():
    channels = ep.get_all_channels()
    return {'channels': [convert_numpy_dict(channel.todict()) 
                         for channel in channels]}

@bottle.get('/excesspower/<ifo>/<subsystem>/<name>')
@bottle.view('excesspower.html')
def get_channel(ifo, subsystem, name):
    try:
        channel = channels.get_channel(ifo, subsystem, name)
        assert ep.has_excess_power(channel)
    except:
        bottle.abort(404, "No such excess power channel.")
        
    with data.read_h5(ep.BURSTS_H5_FILE) as h5:
        bursts = ep.get_bursts_table(channel).attach(h5)
        min_time = bursts[0].start_time
        max_time = bursts[-1].start_time

    return {'root': WEB_ROOT,
            'ifo': ifo,
            'subsystem': subsystem,
            'channel': name,
            'min_time': min_time, 'max_time': max_time,
            'start_time': float(now_as_gps_time())}

@bottle.get('/excesspower/<ifo>/<subsystem>/<name>/summary')
@succeed_or_fail
def get_channel_summary(ifo, subsystem, name):
    channel = channels.get_channel(ifo, subsystem, name)
    with data.read_h5(ep.BURSTS_H5_FILE) as h5:
        bursts = ep.get_bursts_table(channel).attach(h5)
        num_bursts = len(bursts)
        return str(num_bursts)
        last_update = int(bursts.attrs['latest_output_time'])
    return {'channel': channel.todict(), 
            'num_bursts': num_bursts, 
            'last_update': last_update}

@bottle.get('/excesspower/<ifo>/<subsystem>/<name>/bursts_since/<time:int>')
@succeed_or_fail
def get_bursts_since(ifo, subsystem, name, time):
    limit = bottle.request.query.limit or 1000
    channel = channels.get_channel(ifo, subsystem, name)

    with data.read_h5(ep.BURSTS_H5_FILE) as h5:
        table = ep.get_bursts_table(channel).attach(h5)
        bursts = ep.get_bursts_since(table, time, limit=int(limit))

    return {'bursts': map(convert_numpy_dict, bursts)}

@bottle.get('/excesspower/<ifo>/<subsystem>/<name>/bursts/<start_time:int>-<end_time:int>')
@succeed_or_fail
def get_bursts_in_range(ifo, subsystem, name, start_time, end_time):
    limit = bottle.request.query.limit or 100
    channel = channels.get_channel(ifo, subsystem, name)

    with data.read_h5(ep.BURSTS_H5_FILE) as h5:
        table = ep.get_bursts_table(channel).attach(h5)
        bursts = ep.get_bursts_in_time_range(table, 
                 start_time, end_time, limit=int(limit))

    return {'bursts': map(convert_numpy_dict, bursts)}


