
from shared.utils import memoized, float_find_index
import h5py
import numpy as np
from lockfile import LockBase, LockTimeout
from lockfile.mkdirlockfile import MkdirLockFile
from lockfile import LockTimeout
from os.path import join
from functools import wraps
from collections import namedtuple
import time
import os

DATA_DIR = "/home/chase.kernan/data/cmon"
LOCK_DIR = "/home/cgi_output/chase.kernan/"
LOCK_WRITE_TIMEOUT = 10.0
LOCK_READ_TIMEOUT = 5.0
LOCK_POLL = 0.01

# TODO: working, but could use some clean-up
class ReadersWriterLock(object):

    def __init__(self, path, lock_class=MkdirLockFile):
        self.path = path
        self.waiting_lock = lock_class(path + "-waiting", threaded=False)
        self.about_to_write_lock = lock_class(path + "-about_to_write", threaded=False)
        self.write_lock = lock_class(path + "-write", threaded=False)
        self.num_readers_lock = lock_class(path + "-num_readers", threaded=False)
        self.read_lock = lock_class(path + "-read", threaded=False)
        self.num_readers_file = path + "-num_readers_{0}.txt"

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
        with self.waiting_lock:
            with self.num_readers_lock:
                self._local_file = self._get_local_num_readers_file()
                num_readers = self._get_local_num_readers(self._local_file) + 1
                self._set_local_num_readers(self._local_file, num_readers)

                if self._get_total_num_readers() == 1:
                    self.read_lock.acquire()
                    os.chmod(self.read_lock.lock_file, 0o777)

    def release_read(self):
        should_release_read = False
        with self.num_readers_lock:
            num_readers = self._get_local_num_readers(self._local_file) - 1
            self._set_local_num_readers(self._local_file, num_readers)
            if self._get_total_num_readers() == 0 \
                    and not self.about_to_write_lock.is_locked():
                self.read_lock.break_lock()

    # need to have multiple num_readers files so that cgi scripts and cluster
    # processes can both write to them. (Cluster processes can't write to the
    # CGI script num_readers and vice versa, but they can read from all)

    def _get_local_num_readers_file(self):
        for user in range(10):
            try:
                path = self.num_readers_file.format(user)
                with open(path, "a"): pass
                return path
            except IOError as e:
                if e.errno != 13:
                    self._create_num_readers(path)
                    return path

        raise ValueError("Too many users!")

    def _get_local_num_readers(self, file):
        with open(file, "r") as f:
            data = f.read()
        if data:
            return int(data)
        else:
            os.remove(file)
            self._create_num_readers(file)
            return 0

    def _get_total_num_readers(self):
        total = 0
        for user in range(10):
            try:
                with open(self.num_readers_file.format(user), "r") as f:
                    total += int(f.read())
            except IOError as e:
                return total
        raise ValueError("Too many users!")

    def _set_local_num_readers(self, file, num_readers):
        with open(file, "w") as f:
            f.write(str(num_readers))

    def _create_num_readers(self, file):
        handle = os.open(file, os.O_WRONLY|os.O_CREAT, 0o0777)
        os.fdopen(handle, 'w').close()
        with open(file, 'w') as f:
            f.write("0")

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


def open_group(h5, path):
    parts = path.split("/")
    for part in parts[:-1]:
        h5 = h5.require_group(part)
    return h5, parts[-1]


class GenericTable(object):

    def __init__(self, path, dtype=[], chunk_size=10, compression='lzf'):
        # dtype should be a list of ('name', type) tuples
        self.path = path
        self.dtype = dtype
        self.row_class = namedtuple('TableRow', self.column_names)
        self.chunk_size = chunk_size
        self.compression = compression

        self._h5 = None
        self._impl = None

    def attach(self, h5, reset=False):
        if not reset and self._h5 == h5:
            return self._impl

        group, name = open_group(h5, self.path)
        if reset and name in group: 
            del group[name]

        if name in group:
            dataset = group[name]
        else:
            dataset = group.require_dataset(name=name,
                                            shape=(0,),
                                            dtype=self.dtype,
                                            chunks=(self.chunk_size,),
                                            maxshape=(None,),
                                            compression=self.compression,
                                            fletcher32=True,
                                            exact=False)

        self._impl = self.Implementation(self, dataset)
        self._h5 = h5
        return self._impl

    def make_row(self, **fields):
        return self.row_class(*(fields[col] for col in self.column_names))

    @property
    @memoized
    def column_names(self):
        return [field[0] for field in self.dtype]

    class Implementation(object):

        def __init__(self, meta, dataset):
            self._meta = meta
            self._row_class = meta.row_class
            self.dataset = dataset

            try:
                self._length
            except KeyError:
                self._length = 0

        @property
        def columns(self):
            class Columns(object):
                def __getattr__(inner, column):
                    return self.dataset[column][:len(self)]
            return Columns()

        @property
        def attrs(self):
            return self.dataset.attrs

        def read_dict(self, row_index):
            return self.read_row(row_index)._asdict()

        def read_row(self, row_index):
            if row_index >= self._length:
                raise IndexError
            return self._row_class(*self.dataset[row_index])

        def write_dict(self, row_index, **fields):
            self.write_row(row_index, aself.make_row(**fields))

        def write_row(self, row_index, row):
            if row_index >= self._length:
                raise IndexError
            self.dataset[row_index] = row

        def append_dict(self, **fields):
            self.append_row(self.make_row(**fields))

        def append_row(self, row):
            index = self._get_next_index()
            self.dataset[index] = row

        def iterdict(self):
            for i in range(len(self)):
                yield self.read_dict(i)

        def iterrows(self):
            for i in range(len(self)):
                yield self._row_class(*self.dataset[i])

        def __getitem__(self, key):
            if isinstance(key, slice):
                return [self.read_row(i) for i in 
                        xrange(*key.indices(len(self)))]
            else:
                return self.read_row(key)

        def __setitem__(self, key, item):
            if isinstance(key, slice):
                indices = range(*key.indices(len(self)))
                if np.iterable(item):
                    if len(item) != len(indices):
                        raise ValueError
                    for i, row in zip(indices, item):
                        self.write_row(i, row)
                else:
                    if indices[-1] >= self._length:
                        raise IndexError
                    self.dataset[indices] = item
            else:
                self.write_row(key, item)

        def __iter__(self):
            return self.iterrows()

        def __len__(self):
            return self._length

        def __getattr__(self, name):
            return getattr(self._meta, name)

        @property
        def _length(self):
            return self.dataset.attrs["length"]

        @_length.setter
        def _length(self, value):
            self.dataset.attrs["length"] = value

        def _get_next_index(self):
            index = self._length
            if index >= self.dataset.len():
                size = index*2 if index > 0 else 10
                self.dataset.resize((size,))
            self._length = index + 1
            return index


def open_channel(h5, channel, create_if_nonexistent=True):
    if create_if_nonexistent:
        return h5.require_group(channel.type).require_group(channel.name)
    else:
        return h5[channel.type][channel.name]

# TODO! Switch to a subclass of GenericTable instead of duplicating work
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
