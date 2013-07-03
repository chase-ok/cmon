
from shared import dbutils
import numpy as np
import peewee as pw

database = pw.SqliteDatabase(dbutils.make_db_path("rayleigh.db"))

class Frame(pw.Model):
    time = pw.FloatField()
    stride = pw.FloatField()
    num_strides = pw.IntegerField()
    frequencies = dbutils.NumpyField()
    rs = dbutils.NumpyField()

    class Meta:
        database = database

    def as_dict(self):
        return { 'time': self.time,
                 'stride': self.stride,
                 'num_strides': self.num_strides,
                 'frequencies': self.frequencies.tolist(),
                 'rs': self.rs.tolist() }

class Block(pw.Model):
    start_time = pw.FloatField()
    time_offsets = dbutils.NumpyField()
    stride = pw.FloatField()
    num_strides = pw.IntegerField()
    frequencies = dbutils.NumpyField()
    rs = dbutils.NumpyField()

    class Meta:
        database = database

    def bin_frequencies(self, num_bins):
        min_f, max_f = self.frequencies[0], self.frequencies[-1]
        bin_width = (max_f - min_f)/num_bins
        bin_ends = np.linspace(min_f+bin_width, max_f+1e-10, num_bins) 
        bin_indices = np.digitize(self.frequencies, bin_ends)

        binned_rs = np.empty((len(self.time_offsets), num_bins), np.float64)
        for i in range(num_bins):
            binned_rs[:, i] = self.rs[:, bin_indices==i].mean(axis=1)

        self.frequencies = bin_ends - bin_width
        self.rs = binned_rs

    def as_dict(self):
        return { 'start_time': self.start_time,
                 'time_offsets': self.time_offsets.tolist(),
                 'stride': self.stride,
                 'num_strides': self.num_strides,
                 'frequencies': self.frequencies.tolist(),
                 'rs': self.rs.tolist() }

def reset_frames():
    dbutils.reset_table(Frame)

def reset_blocks():
    dbutils.reset_table(Block)

if __name__ == "__main__":
    reset_frames()
    reset_blocks()