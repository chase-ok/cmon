
import bottle
from shared import data, channels as chn, triggers as tr, excesspower, omicron
from shared.utils import now_as_gps_time
from web.utils import *
import numpy as np

@bottle.get('/triggers/<ifo>/<subsystem>/<name>')
@bottle.view('triggers.html')
def get_channel(ifo, subsystem, name):
    source = _get_source()
    try:
        channel = chn.get_channel(ifo, subsystem, name)
        assert tr.has_source(channel, source)
    except:
        bottle.abort(404, "No triggers for {0} provided by {1}"\
                          .format(channel, source))
        
    with data.read_h5(tr.get_h5_file(channel)) as h5:
        triggers = tr.get_table(source).attach(h5)
        min_time = triggers[0].start_time
        max_time = triggers[-1].start_time
        
    time = bottle.request.query.time or now_as_gps_time()

    return {'root': WEB_ROOT,
            'ifo': ifo,
            'subsystem': subsystem,
            'channel': name,
            'source': source.name,
            'min_time': min_time, 'max_time': max_time,
            'start_time': float(time)}


@bottle.get('/triggers/<ifo>/<subsystem>/<name>/<start_time:int>-<end_time:int>')
@succeed_or_fail
def get_triggers_in_range(ifo, subsystem, name, start_time, end_time):
    limit = bottle.request.query.limit or 100
    source = _get_source()
    channel = chn.get_channel(ifo, subsystem, name)

    with data.read_h5(tr.get_h5_file(channel)) as h5:
        table = tr.get_table(source).attach(h5)
        triggers = tr.get_triggers_in_time_range(table, 
                   start_time, end_time, limit=int(limit))

    return {'triggers': map(convert_numpy_dict, triggers)}
    
@bottle.get('/triggers/<ifo>/<subsystem>/<name>/densities')
@succeed_or_fail
def get_densities(ifo, subsystem, name):
    source = _get_source()
    channel = chn.get_channel(ifo, subsystem, name)
    
    freq_bins = tr.DENSITY_FREQ_BINS
    with data.read_h5(tr.get_h5_file(channel)) as h5:
        table = tr.get_density_table(source).attach(h5)
        times = table.dataset[:len(table), "time"]
        densities = table.dataset[:len(table), "density"]

    return {'frequencies': freq_bins.tolist(),
            'times': times.tolist(),
            'densities': densities.tolist()}
    
def _get_source(default="excesspower"):
    source_name = bottle.request.query.source or "excesspower"
    source = tr.find_source(source_name)
    if source is None:
        bottle.abort(404, "No such source: {0}".format(source_name))
    return source
