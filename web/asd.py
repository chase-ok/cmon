
import bottle
from shared.asd import Frame, MovingAverage
from web.utils import *

@bottle.get('/asd')
@bottle.view('asd.html')
def index():
    return {}

@bottle.get('/asd/frames')
@succeed_or_fail
def get_frames():
    query = Frame.select(Frame.time)
    query = add_ordering(query, Frame.time, 'desc')
    query = add_limit(query, None)
    return { 'times': [frame.time for frame in query] }

@bottle.get('/asd/frames/latest')
@succeed_or_fail
@return_model
def get_latest():
    return get_one(Frame.select().order_by(Frame.time.desc()))

@bottle.get('/asd/frames/<time:float>')
@succeed_or_fail
@return_model
def get_frame(time):
    return get_one(Frame.select().where(Frame.time == time))

@bottle.get('/asd/averages')
@succeed_or_fail
def get_averages():
    query = MovingAverage.select(MovingAverage.alpha)
    query = add_ordering(query, MovingAverage.alpha, 'asc')
    query = add_limit(query, None)
    return { 'alphas': [average.alpha for average in query] }

@bottle.get('/asd/averages/<alpha:float>')
@succeed_or_fail
@return_model
def get_average(alpha):
    return get_one(MovingAverage.select().where(MovingAverage.alpha == alpha))

@bottle.post('/asd/averages')
@succeed_or_fail
@return_model
def new_average():
    alpha = float(bottle.request.forms.alpha)
    time = bottle.request.forms.frame_time
    frame = get_frame.raw(float(time)) if time else get_latest.raw()
    
    average = MovingAverage(alpha=alpha,
                            frequencies=frame.frequencies,
                            amplitudes=frame.amplitudes)
    average.save()
    return average

@bottle.delete('/asd/averages/<alpha:float>')
@succeed_or_fail
def delete_average(alpha):
    MovingAverage.delete().where(MovingAverage.alpha == alpha).execute()
    return { 'alpha': alpha }