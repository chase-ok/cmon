
import bottle
from functools import wraps

class QueryError(Exception):
    def __init__(self, reason):
        self.reason = reason
    def __str__(self):
        return "QueryError: {0}".format(self.reason)

def fail(error):
    return { 'success': False, 'error': error }

def succeed(data):
    return { 'success': True, 'data': data }

def succeed_or_fail(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            data = func(*args, **kwargs)
        except Exception as e:
            return fail(str(e))
        return succeed(data)
    return wrapper

def return_model(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs).as_dict()
    wrapper.raw = func
    return wrapper

def add_ordering(query, field, default="desc"):
    order = bottle.request.query.order or default

    try:
        order_func = getattr(field, order)
    except AttributeError:
        raise QueryError('No such ordering: {0}'.format(order))

    return query.order_by(order_func())

def add_limit(query, default=None):
    limit = bottle.request.query.limit or default
    if limit is None: return query

    try:
        limit = int(limit)
        if limit <= 0: 
            raise QueryError('limit must be positive: {0}'.format(limit))
    except ValueError as e:
        raise QueryError(str(e))

    return query.limit(limit)

def get_one(query):
    results = list(query.limit(1))
    if results:
        return results[0]
    else:
        raise QueryError('No such row: {0}'.format(query))