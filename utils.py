
import time

HOME = "/home/chase.kernan"
DATA = "{0}/data/cmon".format(HOME)

def setup_mpl():
    import os    
    os.environ['MPLCONFIGDIR'] = "/tmp/"
    import matplotlib


def make_daemon_loop(name, func, sleep=0, **context_args):
    import sys
    from lockfile.pidlockfile import PIDLockFile

    pidfile = PIDLockFile("{0}/var/{1}_daemon.pid".format(HOME, name))

    assert len(sys.argv) == 2
    cmd = sys.argv[1]

    if cmd == "start": 
        _start_daemon(func, pidfile, sleep, **context_args)
    elif cmd == "stop": 
        _stop_daemon(pidfile)
    elif cmd == "reset":
        _stop_daemon(pidfile)
        _start_daemon(func, pidfile, sleep, **context_args)
    else:
        raise ValueError("Uknown command: {0}".format(cmd))

def _start_daemon(func, pidfile, sleep, **context_args):
    context_args.setdefault("files_preserve", []).append(pidfile)

    import daemon
    with daemon.DaemonContext(working_directory=HOME, 
                              pidfile=pidfile,
                              **context_args):
        while True:
            func()
            if sleep: time.sleep(sleep)

def _stop_daemon(pidfile):
    if pidfile.is_locked():
        import os, signal
        os.kill(pidfile.read_pid(), signal.SIGTERM)
        pidfile.break_lock()
