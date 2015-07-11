"""Frozen dictionary.

Caleb Levy, 2015.
"""

from __future__ import print_function

__all__ = ["frozendict"]


def _frozendict_method(name, map_get):
    """Make wrapper method to access frozendict's internal dict."""
    dict_method = getattr(dict, name)

    def method(self, *args, **kwargs):
        return dict_method(map_get(self), *args, **kwargs)
    method.__name__ = name
    method.__doc__ = dict_method.__doc__
    return method


# Make a function instead of a type so that it does not show up in
# type.__subclasses__(type). I want frozendict to appear like a builtin class,
# which means not exposing implementation details; we don't want spurious
# metaclasses lying around.
#
# (In theory, once we run "del _FrozendictMeta", there should be no further
# references to it, whether it was a type or a function, since we explicitly
# construct frozendict using "type" anyway. However, I have much less faith in
# the garbage collector's ability to deal with metaclasses than with
# functions, since the latter situation comes up much far more often than the
# former, meaning the gc should be tuned to deal with functions quite well.)
def _FrozendictMeta(name, bases, dct):
    """Metaclass helper to form a frozen dictionary.

    _FrozendictMeta allocates a single slot in the template class to
    hold the internal mapping, and then removes that slot's member
    descriptor from the class dict, while retaining a reference to it
    internally.

    It creates wrappers for each of the builtin dict's non-mutating
    methods which access the internal dict using the descriptor.
    Upon returning, all user-accessible references to the descriptor are
    destroyed, leaving no public mechanism to alter the internal dict.
    The resulting class is thus *truly* immutable.

    Note: The process of wrapping these methods provides (IMHO) a nice
    benefit: all methods are guaranteed to be totally independent,
    regardless of any internal relationships between dict methods on
    the python implementation.
    """
    dct['__slots__'] = '_mapping'  # allocate slot for iternal dict
    fd_cls = type(name, bases, dct)  # make template class
    _mapping = fd_cls._mapping  # store reference to descriptor
    del fd_cls._mapping  # destroy external access to the mapping
    del fd_cls.__slots__  # make it look like a builtin type

    # Since the member descriptor's "__set__" and "__get__" methods are
    # themselves (method) descriptors, a new wrapper for them is generated each
    # time they are called. Store references to them locally to avoid this
    # step.
    map_set = _mapping.__set__
    map_get = _mapping.__get__

    # Wrap internal setter inside of __new__
    def __new__(*args, **kwargs):  # signature allows using `cls` keyword arg
        self = super(fd_cls, args[0]).__new__(args[0])
        map_set(self, dict(*args[1:], **kwargs))
        return self
    fd_cls.__new__ = staticmethod(__new__)

    dict_fromkeys = dict.fromkeys  # cache just like for map_get(/set)

    def fromkeys(cls, iterable, v=None):
        """New frozendict with keys from iterable and values set to v."""
        # call cls and copy dict since subclass new might define more
        # conditions (i.e. Multiset)
        return cls(dict_fromkeys(iterable, v))

    fd_cls.fromkeys = classmethod(fromkeys)

    # All of dict's NON-mutating methods.

    # We exclude __del__ since (hopefully) the gc will be unaware that there is
    # a slot without a member descriptor; it should just see a C struct and
    # delete each field. When it sees the internal dict is one of those, it
    # then deletes the dict. (TODO: test the above on different
    # implementations, putting garbage collector benchmarks in the tests.)

    # We exclude __init__ since frozendict is not a dict, and the internal dict
    # is already initialized inside __new__.

    # Exclude __repr__, since we want to wrap it to add "frozendict" around the
    # dict string, so we can't just return dict.__repr__. We exclude __format__
    # and __str__ since they will depend on __repr__.

    # Exclude __setattr__ and __delattr__ since (I believe) those would apply
    # to the internal dict, and just raise AttributeErrors anyway. (TODO:
    # verify this).

    # Exclude the comparison operations since (1) in python3 they just raise
    # TypeErrors, which is equally achievable by no giving them
    # comparison operators in the first place, (2) they should probably have
    # done this in python2 anyway, and (3) the presence of these methods
    # annoyingly prevents using functools.total_ordering in case you DO want a
    # subclass which overrides them, while adding no functionality.

    # Exclude __reduce__ and __reduce_ex__ because I am not sure how dict
    # pickling works, whether the "frozenness" of the dict should impact it,
    # and how I implement whatever I end up deciding to do.
    # (TODO: rectify this bout of laziness on my part).

    dict_methods = [
        '__contains__',
        '__eq__',
        '__getitem__',
        '__iter__',
        '__len__',
        '__ne__',
        'copy',  # no use in returning a new immutable dict, just copy internal
        'get',
        'items',
        'keys',
        'values'
    ]

    # Make frozendict interface resemble dict's as closely as possible.
    # TODO: This may change if it gets annoying.
    if hasattr(dict, 'iterkeys'):
        dict_methods.extend([
            'viewkeys',
            'viewvalues',
            'viewitems',
            'iterkeys',
            'itervalues',
            'iteritems',
            'has_key'
        ])

    if hasattr(dict, '__sizeof__'):  # pypy's dict does not define __sizeof__
        dict_methods.append('__sizeof__')

    for method in dict_methods:
        setattr(fd_cls, method, _frozendict_method(method, map_get))

    # Define here to make all base methods independant

    def __hash__(self):
        return hash(frozenset(map_get(self).items()))
    fd_cls.__hash__ = __hash__

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, map_get(self))
    __repr__.__doc__ = dict.__repr__.__doc__
    fd_cls.__repr__ = __repr__

    return fd_cls


# Must define __doc__ at class creation time sice class docs are not writeable
_fd = \
    """Dictionary with no mutating methods. The values themselves, as
    with tuples, may still be mutable. If all of frozendict's values
    are hashable, then so is frozendict."""

# Declare in a class statement for any metaclass attributes added to the class
# (i.e. cls.__qualname__), and any other nicities added by (C)Python.
if hasattr(dict, 'viewkeys'):
    class frozendict(object):
        __metaclass__ = _FrozendictMeta
        __doc__ = _fd
    del frozendict.__metaclass__
else:
    # six.with_metaclass does not work with functions. Instead we exec it, as
    # there is no other way around a python 2 SyntaxError, which would be
    # raised at *parse* time, before a try-except block can be executed to
    # catch it.
    #
    # Note that we are exec-ing a string literal with no variables or
    # string substitutions. It is thus equivalent to running the line
    # below without the exec and quotes, so we may trust it as such.
    exec("class frozendict(object, metaclass=_FrozendictMeta): __doc__ = _fd")


del _frozendict_method, _FrozendictMeta, _fd


# TODO: Investigate the following:
# 1) Should I add internal _hash cache?
# 2) Are there any MI issues I am not aware of? (Jython, inheriting from base)
# 3) dict(frozendict_subclass) with different __iter__, __copy__, etc...
# 4) Interaction of (3) with registering frozendict as Mapping
# 5) Performance on different implementations
# 6) Inheriting slots with same name?
# 7) Figure out how to shut pylint up about missing methods (because oh God
#    there will be so many...).


if __name__ == '__main__':
    a = frozendict({1: 1, 2: 2, 'a': 3})
    print(a)
    print(repr(a))
    b = dict(a)
    print(b)
    print(b == a)
    print(dir(a))
    db = dir(b)
    for method in ['__setitem__', '__delitem__', 'clear', 'pop',
                   'popitem', 'update', 'setdefault']:
        db.remove(method)
    for attr in dir(a):
        if attr not in db:
            print(attr)
    print(db)
    print(type(frozendict))
    b[1] = 4
    print(a)
    print(b)

    class Multiset(frozendict):
        def __new__(cls, *args, **kwargs):
            print("hi")
            return super(Multiset, cls).__new__(cls, *args, **kwargs)

    at = Multiset({1: "a", 2: "b"})
    bt = Multiset.fromkeys("abc")
    print(bt)
    print(bt)
    print(dict.fromkeys("abc"))
    print(frozendict.__new__ is frozendict.__new__)
    print(frozendict.fromkeys is frozendict.fromkeys)
    c = a.copy()
    print(c)
    c[1] = 'gesture'
    print(c)
    print(a)
