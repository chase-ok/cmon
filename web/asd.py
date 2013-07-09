
import bottle
from shared.asd import read_h5, strain_asd
from web.utils import *


@bottle.get('/asd')
@bottle.view('asd.html')
def index():
    return {}


@bottle.get('/asd/times')
#@succeed_or_fail
def get_times():
    with read_h5() as h5:
        times = strain_asd.attach(h5).times
    times = add_ordering(times)
    times = add_limit(times)
    return {'times': times.tolist()}


@bottle.get('/asd/frequencies')
@succeed_or_fail
def get_frequencies():
    return {'frequencies': strain_asd.calculate_frequencies().tolist()}


@bottle.get('/asd/latest')
@succeed_or_fail
def get_latest():
    with read_h5() as h5:
        time, amplitudes = strain_asd.attach(h5).latest()
    return {'time': float(time), 'amplitudes': amplitudes.tolist()}


@bottle.get('/asd/<time:float>')
@succeed_or_fail
def get_frame(time):
    with read_h5() as h5:
        time, amplitudes = strain_asd.attach(h5).get(time)
    return {'time': float(time), 'amplitudes': amplitudes.tolist()}
