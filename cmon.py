#!/usr/bin/env python

import sys
sys.path.append('/home/chase.kernan/lib64/python2.6/site-packages')

import bottle
from bottle import route, run, request, static_file, view

STATIC_ROOT = '/home/chase.kernan/public_html/cgi-bin/cmon/static'
bottle.TEMPLATE_PATH.append(STATIC_ROOT + "/views/")

from web import asd

@route('/hello')
def hello():
    return "world!"

@route('/static/<filepath:path>')
def server_static(filepath): 
    return static_file(filepath, root=STATIC_ROOT)

run(server="cgi", debug=True)
