
import bottle
from shared.rayleigh import Block
from web.utils import *

@bottle.get('/rayleigh')
@bottle.view('rayleigh.html')
def index():
    return {}

@bottle.get('/rayleigh/blocks')
@succeed_or_fail
def get_blocks():
    query = Block.select(Block.start_time)
    query = add_ordering(query, Block.start_time, 'desc')
    query = add_limit(query, None)
    return { 'start_times': [block.start_time for block in query] }

@bottle.get('/rayleigh/blocks/latest')
@succeed_or_fail
@return_model
def get_latest():
    block = get_one(Block.select().order_by(Block.start_time.desc()))
    num_bins = bottle.request.query.num_frequency_bins
    if num_bins: block.bin_frequencies(int(num_bins))
    return block

@bottle.get('/rayleigh/blocks/<start_time:float>')
@succeed_or_fail
@return_model
def get_block(start_time):
    return get_one(Block.select().where(Block.start_time == time))