
from shared.utils import get_directories, get_files, memoized
from shared.excesspower import *
import os
from os.path import join
import re


_channel_re = re.compile('(?P<subsystem>[A-Z0-9]+)_(?P<channel>[_A-Z0-9]+)_excesspower\\Z')
_time_re = re.compile('(?P<ifo>[A-Z0-9]+)-(?P<subsystem>[A-Z0-9]+)_(?P<channel>[_A-Z0-9]+)_excesspower-(?P<time>[0-9]+)-(?P<duration>[0-9]+)\\.xml\\Z')

def read_channels(root=EXCESS_POWER_ROOT):
    channels = []
    for directory in get_directories(root):
        match = _channel_re.match(directory)
        if not match: continue

        channels.append(Channel(subsystem=match.group('subsystem'),
                                name=match.group('channel'),
                                directory=join(root, directory)))

    return channels

def update_channels_table(h5, root=EXCESS_POWER_ROOT):
    channels = read_channels(root=root)
    table = channels_table.attach(h5, reset=True)
    for channel in channels:
        table.append_dict(**channel.todict())

def read_outputs(channel):
    outputs = []

    for subdir in get_directories(channel.directory):
        try:
            base_time = int(subdir)
            if base_time < 0: raise ValueError
        except ValueError:
            continue

        subdir_path = join(channel.directory, subdir)
        for file in get_files(subdir_path):
            output = _parse_output(channel, subdir_path, file)
            if output: outputs.append(output)

    return outputs 

def read_latest_output(channel):
    subdir = sorted(get_directories(channel.directory), reverse=True)[0]
    subdir_path = join(channel.directory, subdir)

    # abusing that the files are named TIME_DURATION.xml
    # if that ever changes, this method will no longer work
    for file in sorted(get_files(subdir_path), reverse=True):
        output = _parse_output(channel, subdir_path, file)
        if output: return output
    return None

def _parse_output(channel, subdir_path, file):
    match = _time_re.match(file)
    if not match: return None

    assert IFO == match.group('ifo')
    assert channel.subsystem == match.group('subsystem')
    assert channel.name == match.group('channel')

    return Output(channel=channel,
                  time=int(match.group('time')),
                  duration=int(match.group('duration')),
                  path=join(subdir_path, file))

def read_bursts(output):
    from glue.ligolw import ligolw, table, lsctables, utils
    class ContentHandler(ligolw.LIGOLWContentHandler): pass
    table.use_in(ContentHandler)
    lsctables.use_in(ContentHandler)

    xml_doc = utils.load_filename(output.path, contenthandler=ContentHandler)
    return table.get_table(xml_doc, lsctables.SnglBurstTable.tableName)

def append_bursts_to_h5(h5, output, bursts=None):
    if bursts is None:
        bursts = read_bursts(output)

    table = get_bursts_table(output.channel).attach(h5)
    for burst in bursts:
        table.append_row(tuple(getattr(burst, name) for name in 
                               burst_column_names))

    _set_latest_output_time(table, output.time)

def are_bursts_synced(h5, channel):
    table = get_bursts_table(channel).attach(h5)
    latest_table_time = _get_latest_output_time(table)
    latest_file_time = read_latest_output(channel).time
    return latest_table_time == latest_file_time

def sync_bursts(h5, channel):
    table = get_bursts_table(channel).attach(h5)
    latest_table_time = _get_latest_output_time(table)
    to_append = sorted((output for output in read_outputs(channel)
                        if output.time > latest_table_time),
                       key=lambda output: output.time)
    for output in to_append:
        append_bursts_to_h5(h5, output)

def _get_latest_output_time(table):
    return table.attrs.get("latest_output_time", 0)

def _set_latest_output_time(table, time):
    table.attrs["latest_output_time"] = time

def setup_bursts_tables():
    with write_h5() as h5:
        for channel in get_all_channels_from_table(h5):
            get_bursts_table(channel).attach(h5)

def sync_bursts_process(interval=0.5):
    from time import sleep

    while True:
        with read_h5() as h5:
            not_synced = [channel for channel in
                          get_all_channels_from_table(h5)
                          if not are_bursts_synced(h5, channel)]

        for channel in not_synced:
            print "Not synced!", channel
            with write_h5() as h5:
                sync_bursts(h5, channel)

        sleep(interval)

if __name__ == "__main__":
    sync_bursts_process()


