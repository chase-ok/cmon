#!/usr/bin/env python

import bottle
from bottle import route, run, request, static_file, view

STATIC_ROOT = '/home/chase.kernan/public_html/cgi-bin/cmon/static'
bottle.TEMPLATE_PATH.append(STATIC_ROOT + "/views/")

from web import asd

@route('/static/<filepath:path>')
def server_static(filepath): 
    return static_file(filepath, root=STATIC_ROOT)

run(server="cgi", debug=True)
