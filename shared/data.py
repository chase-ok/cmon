
from shared.utils import memoized, float_find_index
import h5py
import numpy as np
from lockfile.linklockfile import LinkLockFile
from os.path import join
from functools import wraps

DATA_DIR = "/home/chase.kernan/data/cmon"
LOCK_TIMEOUT = 15


def make_data_path(name):
    return join(DATA_DIR, name)


class open_h5:

    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs

    def __enter__(self):
        path = make_data_path(self.name)
        self.lock = LinkLockFile(path)
        self.lock.acquire(timeout=LOCK_TIMEOUT)

        self.file = h5py.File(path, *self.args, **self.kwargs)
        return self.file

    def __exit__(self, type, value, traceback):
        self.lock.release()
        self.file.close()


class use_h5:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def __call__(self, f):
        @wraps
        def wrapper(*f_args, **f_kwargs):
            with open_h5(*self.args, **self.kwargs) as h5:
                return f(h5, *f_args, **f_kwargs)
        return wrapper


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
        def times(self):
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
        def frequencies(self):
            name = "{0}_frequencies".format(self.meta.name)
            def create():
                data = self.meta.calculate_frequencies()
                return self.group.create_dataset(name=name, data=data)
            return self._require_array(name, create)

        @property
        @memoized
        def values(self):
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

        def append(self, time, values):
            index = self._get_next_index()
            self.times[index] = time
            self.values[index, :] = values

        @property
        def latest(self):
            index = self._last_index
            if index < 0:
                raise ValueError("No values written yet!")
            return self.times[index], self.values[index, :]

        def get(self, time):
            index = float_find_index(self.times[...], time)
            return self.times[index], self.values[index, :]

        def __iter__(self):
            for i in range(self._last_index):
                yield self.times[i], self.values[i, :]

        def __len__(self):
            return self._last_index

        @property
        def _last_index(self):
            return self.values.attrs["last_index"]

        @_last_index.setter
        def _last_index(self, value):
            self.values.attrs["last_index"] = value

        def _get_next_index(self):
            index = self._last_index + 1
            if index >= self.values.len():
                size = index*2 if index > 0 else 10
                self.values.resize(size, axis=0)
                self.times.resize((size,))
            self._last_index = index
            return index

        def _require_array(self, name, create_func):
            try:
                return self.group[name]
            except KeyError:
                return create_func()
