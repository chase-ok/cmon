
from shared import data, channels as chn, triggers as tr
from shared.utils import get_directories, get_files, memoized
from lockfile import LockTimeout
import os
from os.path import join
import re
import logging
import numpy as np
import bisect
from xml.sax._exceptions import SAXException


CHANNEL_RE_TEMPLATE = r'(?P<subsystem>[A-Z0-9]+)\-(?P<channel>[_A-Z0-9]+)_{0.name}\Z'
@memoized
def _get_channel_re(source): 
    return re.compile(CHANNEL_RE_TEMPLATE.format(source))

FAKE_CHANNEL_RE_TEMPLATE = r'FAKE_(?P<channel>[_A-Z0-9]+)_{0.name}\Z'
@memoized
def _get_fake_channel_re(source): 
    return re.compile(FAKE_CHANNEL_RE_TEMPLATE.format(source))

TIME_RE_TEMPLATE = r'(?P<ifo>[A-Z0-9]+)-(?P<subsystem>[A-Z0-9]+)_(?P<channel>[_A-Z0-9]+)_{0.name}-(?P<time>[0-9]+)-(?P<duration>[0-9]+)\.xml\Z'
@memoized
def _get_time_re(source): 
    return re.compile(TIME_RE_TEMPLATE.format(source))


def update_channels(source):
    channels = []
    for ifo in get_directories(source.root):
        for directory in get_directories(join(source.root, ifo)):
            match = _get_channel_re(source).match(directory)
            if match:
                channels.append(tr.add_channel(source, ifo, 
                                               match.group('subsystem'),
                                               match.group('channel')))
                continue
            
            match = _get_fake_channel_re(source).match(directory)
            if match:
                channels.append(tr.add_channel(source, ifo, 
                                               'FAKE', match.group('channel')))
                continue
            
            logging.warn('Unknown directory: {0}'.format(directory))
    
    with data.write_h5(chn.H5_FILE) as h5:
        all_channels = chn.get_all_channels(h5=h5)
        for channel in all_channels:
            if channel not in channels:
                tr.set_not_source(channel, source)


def get_trigger_files(source, channel):
    files = []
    
    dir = tr.get_trigger_directory(source, channel)
    for subdir in get_directories(dir):
        try:
            base_time = int(subdir)
            if base_time < 0: raise ValueError
        except ValueError: continue

        subdir_path = join(dir, subdir)
        for file in get_files(subdir_path):
            file = _parse_trigger_file_path(source, channel, subdir_path, file)
            if file: files.append(file)
    
    return files


def get_latest_trigger_file(source, channel):
    dir = tr.get_trigger_directory(source, channel)
    subdir = sorted(get_directories(dir), reverse=True)[0]
    subdir_path = join(dir, subdir)
    
    # abusing that the files are named ...{TIME}_{DURATION}.xml
    # if that ever changes, this method will no longer work
    for file in sorted(get_files(subdir_path), reverse=True):
        file = _parse_trigger_file_path(source, channel, subdir_path, file)
        if file: return file
    return None


def _parse_trigger_file_path(source, channel, subdir_path, file):
    match = _get_time_re(source).match(file)
    if not match: return None
    
    if channel.ifo != match.group('ifo')\
            or channel.subsystem != match.group('subsystem')\
            or channel.name != match.group('channel'):
        logging.warning("Bad file name {0}".format(file))
        return None

    return tr.File(source=source,
                   channel=channel,
                   time=int(match.group('time')),
                   duration=int(match.group('duration')),
                   path=join(subdir_path, file))


def read_triggers(trigger_file):
    from glue.ligolw import array, param, ligolw, table, lsctables, utils
    class ContentHandler(ligolw.LIGOLWContentHandler): pass
    for module in [array, param, table, lsctables]:
        module.use_in(ContentHandler)

    xml_doc = utils.load_filename(trigger_file.path,
                                  contenthandler=ContentHandler)
    return table.get_table(xml_doc, lsctables.SnglBurstTable.tableName)


def append_triggers_to_h5(trigger_file, triggers=None, h5=None):
    if triggers is None:
        try:
            triggers = read_triggers(trigger_file)
        except SAXException as e:
            logging.error('Bad file {0.path}: {1}'.format(trigger_file, e))
            return
    
    with data.write_h5(tr.get_h5_file(trigger_file.channel), existing=h5) as h5:
        table = tr.get_table(trigger_file.source).attach(h5)
        for trigger in triggers:
            table.append_row(tuple(getattr(trigger, name) for name in 
                                   tr.COLUMN_NAMES))
        
        tr.set_last_updated(table, trigger_file.time)


def are_triggers_synced(source, channel, h5=None):
    latest_file = get_latest_trigger_file(source, channel)
    if latest_file is None: 
        logging.warn("No trigger files for {0} in {1}".format(source, channel))
        return True

    latest_file_time = latest_file.time
    with data.read_h5(tr.get_h5_file(channel), existing=h5) as h5:
        table = tr.get_table(source).attach(h5)
        return tr.get_last_updated(table) == latest_file_time


def sync_triggers(source, channel):
    with data.read_h5(tr.get_h5_file(channel)) as h5:
        table = tr.get_table(source).attach(h5)
        latest_table_time = tr.get_last_updated(table)
    
    to_append = sorted((file for file in get_trigger_files(source, channel)
                        if file.time > latest_table_time),
                       key=lambda file: file.time)

    logging.debug("Syncing {0} files...".format(len(to_append)))
    print "Syncing {0} files...".format(len(to_append))
    with data.write_h5(tr.get_h5_file(channel)) as h5:
        for i, file in enumerate(to_append):
            if i % 100 == 0: 
                logging.debug("{0} completed".format(i))
                print "{0} completed".format(i)
            
            append_triggers_to_h5(file, h5=h5)


def setup_tables(source, h5=None):
    for channel in tr.get_all_channels(source):
        with data.write_h5(tr.get_h5_file(channel)) as h5:
            table = tr.get_table(source).attach(h5)    


def sync_triggers_process(source, interval=0.5):
    from time import sleep

    while True:
        logging.debug("Checking triggers in {0.name}...".format(source))
        print "Checking triggers in {0.name}...".format(source)
        not_synced = [channel for channel in tr.get_all_channels(source)
                      if not are_triggers_synced(source, channel)]

        for channel in not_synced:
            logging.debug("Not synced {0}!".format(channel))
            print "Not synced {0}!".format(channel)
            try:
                sync_triggers(source, channel)
            except LockTimeout:
                logging.warning("Lock timeout on {0}.".format(channel))
                print "Lock timeout on {0}.".format(channel)

        sleep(interval)


def compute_densities(source, channel):
    with data.write_h5(tr.get_h5_file(channel)) as h5:
        triggers = tr.get_table(source).attach(h5)
        densities = tr.get_density_table(source).attach(h5, reset=True)
        
        index = 0
        num_triggers = len(triggers)
        bins = tr.DENSITY_FREQ_BINS
        num_bins = len(bins)
        
        start = triggers[0].start_time
        end = triggers[num_triggers-1].start_time
        assert start < end
        
        sums = np.zeros_like(bins).astype(np.float32)
        for chunk in range(start, end, tr.DENSITY_TIME_CHUNK):            
            cutoff = chunk + tr.DENSITY_TIME_CHUNK
            
            sums.fill(0)
            while index < num_triggers:
                trigger = triggers[index]
                if trigger.start_time > cutoff: break
                
                bin = min(num_bins-1, bisect.bisect(bins, trigger.central_freq))
                sums[bin] += trigger.snr*trigger.duration*trigger.bandwidth
                index += 1
            
            densities.append_row((chunk, sums/tr.DENSITY_TIME_CHUNK))
            print chunk, sums

