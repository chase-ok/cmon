
import time

HOME = "/home/chase.kernan"
DATA = "{0}/data/cmon".format(HOME)

def setup_mpl():
    import os    
    os.environ['MPLCONFIGDIR'] = "/tmp/"
    import matplotlib

def now_as_gps_time():
    from glue.gpstime import GpsSecondsFromPyUTC
    return GpsSecondsFromPyUTC(time.time())


def make_daemon_loop(name, func, sleep=0):
    import sys
    from lockfile.pidlockfile import PIDLockFile

    pidfile = PIDLockFile("{0}/var/{1}_daemon.pid".format(HOME, name))

    assert len(sys.argv) == 2
    cmd = sys.argv[1]

    if cmd == "start": 
        _start_daemon(func, pidfile, sleep)
    elif cmd == "stop": 
        _stop_daemon(pidfile)
    elif cmd == "reset":
        _stop_daemon(pidfile)
        _start_daemon(func, pidfile, sleep)
    else:
        raise ValueError("Uknown command: {0}".format(cmd))

def _start_daemon(func, pidfile, sleep):
    import daemon
    with daemon.DaemonContext(working_directory=HOME, 
                              pidfile=pidfile,
                              files_preserve=[pidfile]):
        while True:
            func()
            if sleep: time.sleep(sleep)

def _stop_daemon(pidfile):
    if pidfile.is_locked():
        import os, signal
        os.kill(pidfile.read_pid(), signal.SIGTERM)
        pidfile.break_lock()
    


    
    