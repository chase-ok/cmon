
from shared import dbutils
import peewee as pw

database = pw.SqliteDatabase(dbutils.make_db_path("asd.db"))

class Frame(pw.Model):
    time = pw.FloatField()
    duration = pw.FloatField()
    frequencies = dbutils.NumpyField()
    amplitudes = dbutils.NumpyField()

    class Meta:
        database = database

    def as_dict(self):
        return { 'time': self.time,
                 'duration': self.duration,
                 'frequencies': self.frequencies.tolist(),
                 'amplitudes': self.amplitudes.tolist() }

class MovingAverage(pw.Model):
    alpha = pw.FloatField()
    frequencies = dbutils.NumpyField()
    amplitudes = dbutils.NumpyField()

    def as_dict(self):
        return { 'alpha': self.alpha,
                 'frequencies': self.frequencies.tolist(),
                 'amplitudes': self.amplitudes.tolist() }

def reset_frames():
    dbutils.reset_table(Frame)

def reset_averages():
    dbutils.reset_table(MovingAverage)
