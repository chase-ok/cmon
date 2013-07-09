
import bottle
import numpy as np
from functools import wraps


class QueryError(Exception):
    def __init__(self, reason):
        self.reason = reason

    def __str__(self):
        return "QueryError: {0}".format(self.reason)


def fail(error):
    return {'success': False, 'error': error}


def succeed(data):
    return {'success': True, 'data': data}


def succeed_or_fail(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            data = func(*args, **kwargs)
        except Exception as e:
            return fail(str(e))
        return succeed(data)
    return wrapper


def add_ordering(values, default=None):
    order = bottle.request.query.order or default

    if order is None or order.tolower() == "none":
        return values
    elif order.tolower() == "asc":
        return np.sort(values)
    elif order.tolower() == "desc":
        return np.sort(values)[::-1]
    else:
        raise QueryError('No such ordering: {0}'.format(order))


def add_limit(values, default=None):
    limit = bottle.request.query.limit or default
    if limit is None:
        return values

    try:
        limit = int(limit)
        if limit <= 0:
            raise QueryError('limit must be positive: {0}'.format(limit))
    except ValueError as e:
        raise QueryError(str(e))

    return values[:limit]
