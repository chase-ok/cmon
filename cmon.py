#!/usr/bin/env python

import sys
sys.path.append('/home/chase.kernan/lib64/python2.6/site-packages')
sys.path.append('/usr/lib64/python2.6/site-packages')

import logging
logging.basicConfig(filename='cmon-web.log')

import bottle
from bottle import route, run, request, static_file, view
from web.utils import succeed_or_fail

STATIC_ROOT = '/home/chase.kernan/public_html/cgi-bin/cmon/static'
bottle.TEMPLATE_PATH.append(STATIC_ROOT + "/views/")

from web import asd, excesspower

@route('/time')
@succeed_or_fail
def get_time():
    from shared.utils import now_as_gps_time
    return {'time': str(now_as_gps_time())}

@route('/static/<filepath:path>')
def server_static(filepath): 
    return static_file(filepath, root=STATIC_ROOT)

run(server="cgi", debug=True)
