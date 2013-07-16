
from shared import data, channels as chn, excesspower as ep
from shared.utils import get_directories, get_files, memoized
import os
from os.path import join
import re
import logging
from xml.sax._exceptions import SAXException

_channel_re = re.compile(r'(?P<subsystem>[A-Z0-9]+)\-(?P<channel>[_A-Z0-9]+)_excesspower\Z')
_fake_channel_re = re.compile(r'FAKE_(?P<channel>[_A-Z0-9]+)_excesspower\Z')
_time_re = re.compile('(?P<ifo>[A-Z0-9]+)-(?P<subsystem>[A-Z0-9]+)_(?P<channel>[_A-Z0-9]+)_excesspower-(?P<time>[0-9]+)-(?P<duration>[0-9]+)\\.xml\\Z')

def update_channels(root=ep.TRIGGERS_ROOT):
    for ifo in get_directories(root):
        for directory in get_directories(join(root, ifo)):
            match = _channel_re.match(directory)
            if match:
                ep.add_channel(ifo=ifo, 
                               subsystem=match.group('subsystem'),
                               name=match.group('channel'))
                continue
            
            match = _fake_channel_re.match(directory)
            if match:
                ep.add_channel(ifo=ifo,
                               subsystem='FAKE',
                               name=match.group('channel'))
                continue
            
            logging.warn('Unknown directory: {0}'.format(directory))


def get_trigger_files(channel):
    files = []
    
    dir = ep.get_trigger_directory(channel)
    for subdir in get_directories(dir):
        try:
            base_time = int(subdir)
            if base_time < 0: raise ValueError
        except ValueError: continue

        subdir_path = join(dir, subdir)
        for file in get_files(subdir_path):
            file = _parse_trigger_file_path(channel, subdir_path, file)
            if file: files.append(file)
    
    return files


def get_latest_trigger_file(channel):
    dir = ep.get_trigger_directory(channel)
    subdir = sorted(get_directories(dir), reverse=True)[0]
    subdir_path = join(dir, subdir)
    
    # abusing that the files are named ...{TIME}_{DURATION}.xml
    # if that ever changes, this method will no longer work
    for file in sorted(get_files(subdir_path), reverse=True):
        file = _parse_trigger_file_path(channel, subdir_path, file)
        if file: return file
    return None


def _parse_trigger_file_path(channel, subdir_path, file):
    match = _time_re.match(file)
    if not match: return None

    assert channel.ifo == match.group('ifo')
    assert channel.subsystem == match.group('subsystem')
    assert channel.name == match.group('channel')

    return ep.TriggerFile(channel=channel,
                          time=int(match.group('time')),
                          duration=int(match.group('duration')),
                          path=join(subdir_path, file))


def read_bursts(trigger_file):
    from glue.ligolw import array, param, ligolw, table, lsctables, utils
    class ContentHandler(ligolw.LIGOLWContentHandler): pass
    for module in [array, param, table, lsctables]:
        module.use_in(ContentHandler)

    xml_doc = utils.load_filename(trigger_file.path,
                                  contenthandler=ContentHandler)
    return table.get_table(xml_doc, lsctables.SnglBurstTable.tableName)


@data.use_h5(ep.H5_FILE, 'w')
def append_bursts_to_h5(trigger_file, bursts=None, h5=None):
    if bursts is None:
        try:
            bursts = read_bursts(trigger_file)
        except SAXException as e:
            logging.error('Bad file {0.path}: {1}'.format(trigger_file, e))
            return

    table = ep.get_bursts_table(trigger_file.channel).attach(h5)
    for burst in bursts:
        table.append_row(tuple(getattr(burst, name) for name in 
                               ep.BURST_COLUMN_NAMES))

    _set_latest_trigger_time(table, trigger_file.time)


@data.use_h5(ep.H5_FILE, 'r')
def are_bursts_synced(channel, h5=None):
    table = ep.get_bursts_table(channel).attach(h5)
    latest_table_time = _get_latest_trigger_time(table)
    latest_file_time = get_latest_trigger_file(channel).time
    return latest_table_time == latest_file_time


def sync_bursts(channel):
    with data.read_h5(ep.H5_FILE) as h5:
        table = ep.get_bursts_table(channel).attach(h5)
        latest_table_time = _get_latest_trigger_time(table)
        to_append = sorted((file for file in get_trigger_files(channel)
                            if file.time > latest_table_time),
                           key=lambda file: file.time)

    #logging.debug("Syncing {0} files...".format(len(to_append)))
    print "Syncing {0} files...".format(len(to_append))
    for i, file in enumerate(to_append):
        if i % 100 == 0: 
            #logging.debug("{0} completed".format(i))
            print "{0} completed".format(i)
        append_bursts_to_h5(file)


def _get_latest_trigger_time(table):
    return table.attrs.get("latest_trigger_time", 0)

def _set_latest_trigger_time(table, time):
    table.attrs["latest_trigger_time"] = time


@data.use_h5(ep.H5_FILE, 'w')
def setup_bursts_tables(h5=None):
    for channel in ep.get_all_channels():
        ep.get_bursts_table(channel).attach(h5)


def sync_bursts_process(interval=0.5):
    from time import sleep

    while True:
        #logging.debug("Checking bursts...")
        print "Checking bursts"
        with data.read_h5(ep.H5_FILE) as h5:
            not_synced = [channel for channel in ep.get_all_channels()
                          if not are_bursts_synced(channel, h5=h5)]

        for channel in not_synced:
            #logging.debug("Not synced {0}!".format(channel))
            print "Not synced {0}!".format(channel)
            sync_bursts(channel)

        sleep(interval)


if __name__ == "__main__":
    sync_bursts_process()
