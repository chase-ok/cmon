
import utils
import os
from os.path import join, samefile
import subprocess
import logging

DIRECTORY = "."
UPLOAD_SCRIPT = "upload"
LOG_FILE = "./sftp.log"
GRID_URL = "ldas-grid.ligo.caltech.edu"
UPLOAD_DIRECTORY = "/home/chase.kernan/public_html/cgi-bin/cmon"

_mod_times = dict()

def daemon():
    _to_upload = []

    for root, dirs, files in os.walk(DIRECTORY):
        for name in files:
            path = join(root, name)[2:]
            if samefile(UPLOAD_SCRIPT, path) or samefile(LOG_FILE, path):
                continue

            mod_time = get_mod_time(path)
            try:
                if mod_time > _mod_times[path]:
                    _to_upload.append(path)
            except KeyError:
                _to_upload.append(path)
            _mod_times[path] = mod_time

    logging.debug(str(_to_upload))
    with open(UPLOAD_SCRIPT, "w") as f:
        for path in _to_upload:
            f.write("put {0} {0}\n".format(path))

    with open(os.devnull, "w") as null:
        subprocess.call("gsisftp -b {0} {1}:{2}"\
                        .format(UPLOAD_SCRIPT, GRID_URL, UPLOAD_DIRECTORY),
                        shell=True,
                        stdout=null)

def upload(path):
    subprocess.call()

def get_mod_time(path):
    return os.stat(path).st_mtime

if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(LOG_FILE)
    logger.addHandler(fh)

    import time
    while True:
        daemon()
        time.sleep(0.1)

    #utils.HOME = "/home/ckernan"
    #utils.make_daemon_loop("sftp", daemon, sleep=1,
    #                       files_preserve=[fh.stream])