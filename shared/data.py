
from shared.utils import memoized, float_find_index
import h5py
import numpy as np
from lockfile import LockBase, LockTimeout
from lockfile.mkdirlockfile import MkdirLockFile
from lockfile import LockTimeout
from os.path import join
from functools import wraps
import time
import os

DATA_DIR = "/home/chase.kernan/data/cmon"
LOCK_DIR = "/home/cgi_output/chase.kernan/"
LOCK_WRITE_TIMEOUT = 10.0
LOCK_READ_TIMEOUT = 5.0
LOCK_POLL = 0.01

class ReadersWriterLock(object):

    def __init__(self, path, lock_class=MkdirLockFile):
        self.path = path
        self.waiting_lock = lock_class(path + "-waiting", threaded=False)
        self.about_to_write_lock = lock_class(path + "-about_to_write", threaded=False)
        self.write_lock = lock_class(path + "-write", threaded=False)
        self.num_readers_lock = lock_class(path + "-num_readers", threaded=False)
        self.read_lock = lock_class(path + "-read", threaded=False)
        self.num_readers_file = path + "-num_readers.txt"

    def acquire_write(self):
        self.waiting_lock.acquire(timeout=LOCK_WRITE_TIMEOUT)

        try:
            self._wait_on(self.num_readers_lock, LOCK_WRITE_TIMEOUT)
            self.read_lock.acquire(timeout=LOCK_WRITE_TIMEOUT)
        except LockTimeout:
            self.waiting_lock.release()
            raise
        try:
            self.about_to_write_lock.acquire(timeout=LOCK_WRITE_TIMEOUT)
        except LockTimeout:
            self.read_lock.release()
            self.waiting_lock.release()
            raise
        try:
            self.write_lock.acquire(timeout=LOCK_WRITE_TIMEOUT)
        except LockTimeout:
            self.about_to_write_lock.release()
            self.read_lock.release()
            self.waiting_lock.release()
            raise

        self.about_to_write_lock.release()

    def release_write(self):
        self.write_lock.release()
        self.read_lock.release()
        self.waiting_lock.release()

    def acquire_read(self):
        self._wait_on(self.waiting_lock, LOCK_READ_TIMEOUT)

        with self.num_readers_lock:
            if not os.path.exists(self.num_readers_file):
                self._create_num_readers()
                num_readers = 1
            else:
                num_readers = self._get_num_readers() + 1
            self._set_num_readers(num_readers)

            if num_readers == 1:
                self.read_lock.acquire()
                os.chmod(self.read_lock.lock_file, 0o777)

    def release_read(self):
        should_release_read = False
        with self.num_readers_lock:
            num_readers = self._get_num_readers() - 1
            self._set_num_readers(num_readers)
            if num_readers == 0 and not self.about_to_write_lock.is_locked():
                self.read_lock.break_lock()

    def _get_num_readers(self):
        with open(self.num_readers_file, "r") as f:
            return int(f.read())

    def _set_num_readers(self, num_readers):
        with open(self.num_readers_file, "w") as f:
            f.write(str(num_readers))

    def _create_num_readers(self):
        file = os.open(self.num_readers_file, os.O_WRONLY|os.O_CREAT, 0o777)
        os.fdopen(file, 'w').close()

    def _wait_on(self, lock, timeout):
        end_time = time.time() + timeout
        while lock.is_locked():
            if time.time() > end_time:
                raise LockTimeout
            time.sleep(LOCK_POLL)

def _make_data_path(name):
    return join(DATA_DIR, name)

def _make_lock_path(name):
    return join(LOCK_DIR, name)

class write_h5:

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.lock = ReadersWriterLock(_make_lock_path(self.name))
        self.lock.acquire_write()
        self.h5 = h5py.File(_make_data_path(self.name), mode="a")
        return self.h5

    def __exit__(self, type, value, traceback):
        self.h5.flush()
        self.h5.close()
        self.lock.release_write()

class read_h5:

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        self.lock = ReadersWriterLock(_make_lock_path(self.name))
        self.lock.acquire_read()
        self.h5 = h5py.File(_make_data_path(self.name), mode="r")
        return self.h5

    def __exit__(self, type, value, traceback):
        self.h5.close()
        self.lock.release_read()

class GenericTable(object):

    def __init__(self, name, columns=[]):
        pass

def open_channel(h5, channel, create_if_nonexistent=True):
    if create_if_nonexistent:
        return h5.require_group(channel.type).require_group(channel.name)
    else:
        return h5[channel.type][channel.name]


class SpectralTable(object):

    def __init__(self, name, channel, seglen=2**14, stride=None):
        self.name = name
        self.channel = channel
        self.seglen = seglen
        self.stride = stride or seglen

    def calculate_frequencies(self):
        #f0 = 1.0/(channels.delta_t(self.meta.channel)*self.meta.seglen)
        #delta_f = 1.0/self.meta.seglen
        #indices = np.arange(self.meta.seglen//2 + 1, dtype=np.float32)
        #return indices*delta_f + f0
        return np.arange(self.seglen//2 + 1, dtype=np.float64)

    def attach(self, h5):
        return self.Implementation(open_channel(h5, self.channel), self)

    class Implementation(object):

        def __init__(self, group, meta):
            self.group = group
            self.meta = meta

        @property
        @memoized
        def frequencies(self):
            name = "{0}_frequencies".format(self.meta.name)
            def create():
                data = self.meta.calculate_frequencies()
                return self.group.create_dataset(name=name, data=data)
            return self._require_array(name, create)

        @property
        def times(self):
            return self._times[:self._last_index+1]

        @property
        def values(self):
            return self._values[:self._last_index+1, ...]

        def append(self, time, values):
            index = self._get_next_index()
            self._times[index] = time
            self._values[index, :] = values

        def latest(self):
            index = self._last_index
            if index < 0:
                raise ValueError("No values written yet!")
            return self._times[index], self._values[index, :]

        def get(self, time):
            index = float_find_index(self.times, time)
            return self.times[index], self.values[index, :]

        def __iter__(self):
            for i in range(self._last_index):
                yield self.times[i], self.values[i, :]

        def __len__(self):
            return self._last_index+1

        @property
        @memoized
        def _times(self):
            name = "{0}_times".format(self.meta.name)
            def create():
                return self.group.create_dataset(name=name,
                                                 shape=(0,),
                                                 dtype=np.float32,
                                                 chunks=(128,),
                                                 maxshape=(None,))
            return self._require_array(name, create)

        @property
        @memoized
        def _values(self):
            def create():
                length = self.frequencies.len()
                dataset = self.group.require_dataset(name=self.meta.name,
                                                     shape=(0, length),
                                                     dtype=np.float64,
                                                     chunks=(1, length),
                                                     maxshape=(None, length),
                                                     compression='lzf',
                                                     fletcher32=True,
                                                     exact=True)
                self._last_index = -1

                #dataset.dims.create_scale(self.times, "times")
                #dataset.dims[0].attach_scale(self.times)
                #dataset.dims.create_scale(self.frequencies, "frequencies")
                #dataset.dims[1].attach_scale(self.frequencies)

                return dataset
            return self._require_array(self.meta.name, create)

        @property
        def _last_index(self):
            return self._values.attrs["last_index"]

        @_last_index.setter
        def _last_index(self, value):
            self._values.attrs["last_index"] = value

        def _get_next_index(self):
            index = self._last_index + 1
            if index >= self._values.len():
                size = index*2 if index > 0 else 10
                self._values.resize(size, axis=0)
                self._times.resize((size,))
            self._last_index = index
            return index

        def _require_array(self, name, create_func):
            try:
                return self.group[name]
            except KeyError:
                return create_func()
