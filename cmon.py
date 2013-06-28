#!/usr/bin/env python
import bottle
from bottle import route, run, static_file, view, template
import utils
import urllib2

STATIC_ROOT = '/home/chase.kernan/public_html/cgi-bin/cmon/static'
bottle.TEMPLATE_PATH.append(STATIC_ROOT + "/views/")

@route('/hello')
def hello(): 
    return urllib2.urlopen("http://localhost:8080/hello").read()

@route('/static/<filepath:path>')
def server_static(filepath): 
    return static_file(filepath, root=STATIC_ROOT)

@route('/asd')
@view("asd.html")
def asd(): return {}

@route('/asd/data')
def asd_data():
    import asd 
    return asd.read_from_daemon(native_python=True)

@route('/asd/<start_time:int>_<duration:int>')
def asd(start_time, duration):
    import asd
    return asd.compute_asd(start_time, duration)

run(server="cgi", debug=True)