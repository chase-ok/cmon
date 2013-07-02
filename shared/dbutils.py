
import peewee as pw
from cStringIO import StringIO
import numpy as np
from os.path import join

DB_DIR = "/home/chase.kernan/data/cmon"
def make_db_path(name):
    return join(DB_DIR, name)

class NumpyField(pw.Field):
    db_field = 'blob'

    def db_value(self, value):
        output = StringIO()
        np.save(output, value)
        return buffer(output.getvalue())
    
    def python_value(self, value):
        input = StringIO(value)
        return np.load(input)

def reset_table(model):
    if model.table_exists(): model.drop_table()
    model.create_table()

def limit_1(query, error_on_more=False):
    result = list(query.limit(1))
    if error_on_more: assert len(result) <= 1
    return result[0] if result else None