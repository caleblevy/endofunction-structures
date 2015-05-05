"""Module for computing conjugacy classes of self mappings on floating point
numbers.

Caleb Levy, 2015.
"""

import numbers
import unittest

import numpy as np

from funcstructs import *

__all__ = [
    "Inf", "Zero", "One", "NaN", "Min16", "Max16",
    "Positives", "Negatives", "FinitePositives", "FiniteNegatives",
    "NonPositives", "NonNegatives", "FiniteNonPositives", "FiniteNonNegatives",
    "UnitInterval", "Finites", "NonNan", "Floats"
]


Inf = np.float16('inf')
NaN = np.float16('nan')
Max16 = np.float16(65504.0)
Min16 = -Max16
Zero = np.float16(0)
One = np.float16(1)


def nextfloat(f): return np.nextafter(f, Inf, dtype=np.float16)


def prevfloat(f): return np.nextafter(f, -Inf, dtype=np.float16)


class FloatSet(tuple):
    """tuple of floats with constant time membership testing"""
    def __init__(self, _):
        self._elems = frozenset(self)

        if len(self._elems) != len(self):
            raise ValueError("Elements of float domain must be unique")
        if not all(type(f) is np.float16 for f in self):
            raise TypeError("FloatSet must contain float16")

        self._intmap = {}
        for i, f in enumerate(self):  # Create the inverse map
            self._intmap[f] = i

    def __contains__(self, item):
        return item in self._elems

    def __add__(self, other):
        return self.__class__(tuple(self) + tuple(other))

    def __radd__(self, other):
        return self.__class__(tuple(other) + tuple(self))

    def __getitem__(self, key):
        if isinstance(key, np.float16):
            return self._intmap[key]
        elif isinstance(key, slice):
            return self.__class__(super(FloatSet, self).__getitem__(key))
        return super(FloatSet, self).__getitem__(key)  # integer case

    # python2 compatibility function
    def __getslice__(self, start, stop):
        return self.__class__(super(FloatSet, self).__getslice__(start, stop))

    def conj(self, f):
        """Conjugate func into integer domain"""
        _sentinal = object()
        fi = [_sentinal] * len(self)
        for x, y in f.items():
            try:
                fi[self[x]] = self[y]
            except KeyError:
                if np.isnan(y):
                    fi[self[x]] = self[NaN]
                else:
                    raise
        if _sentinal in fi:
            raise ValueError("Incompatible domains")
        return Endofunction(fi)

    def endofunction(self, mapping):
        """Make endofunction from mapping applied to the domain"""
        f = {}
        for x in self:
            f[x] = mapping(x)
        return self.conj(f)

    def structure(self, mapping):
        """Return structure of endofunction generated by mapping"""
        return Funcstruct.from_func(self.endofunction(mapping))


Negatives = [-Inf]
f = Min16
while f < Zero:
    Negatives.append(f)
    f = nextfloat(f)
Negatives = FloatSet(Negatives)

f = nextfloat(Zero)
Positives = [f]
while f < Max16:
    f = nextfloat(f)
    Positives.append(f)
del f

Positives.append(Inf)
Positives = FloatSet(Positives)

NonPositives = Negatives + (Zero, )
NonNegatives = (Zero, ) + Positives

FinitePositives = Positives[:-1]
FiniteNonNegatives = NonNegatives[:-1]
FiniteNegatives = Negatives[1:]
FiniteNonPositives = NonPositives[1:]

UnitInterval = NonNegatives[:NonNegatives[One]+1]
Finites = FiniteNegatives + FiniteNonNegatives
NonNan = Negatives + NonNegatives
Floats = (NaN, ) + NonNan


class FloatSetTests(unittest.TestCase):

    finite = [Min16, Zero, One, Max16]
    nonfinite = [-Inf, NaN, Inf]
    fin = FloatSet(finite)
    nfi = FloatSet(nonfinite)

    def test_init_errors(self):
        # Make sure error is raised for non-float16
        with self.assertRaises(TypeError):
            FloatSet([np.float32('inf')])
        with self.assertRaises(TypeError):
            FloatSet([np.float64('nan'), 1, 2])
        # Make sure duplicates are not allowed
        with self.assertRaises(ValueError):
            FloatSet(self.finite + self.finite)

    def test_addition(self):
        # Cannot add elements with duplicates
        with self.assertRaises(ValueError):
            self.fin + self.fin
        e = self.fin + self.nfi
        self.assertEqual(7, len(e))
        for f in self.finite + self.nonfinite:
            self.assertIn(f, e)

    def test_float_lists(self):
        for fset in [
            Negatives, NonNegatives, Positives, NonPositives,
            FiniteNonNegatives, FiniteNonPositives, FiniteNegatives,
            FinitePositives, UnitInterval, Finites, NonNan, Floats
        ]:
            self.assertIsInstance(fset, FloatSet)

    def test_conjugation(self):
        f = {x: x for x in self.finite}
        g = {x: x for x in self.finite[:-1]}
        h = {x: x for x in self.nonfinite}
        # Order should be independent of dict
        self.assertEqual(
            Endofunction(range(4)),
            self.fin.conj(f)
        )
        self.assertEqual(
            Endofunction(range(3)),
            self.nfi.conj(h)
        )
        # Subdomain
        with self.assertRaises(ValueError):
            self.fin.conj(g)
        # Wrong domain
        with self.assertRaises(KeyError):
            self.fin.conj(h)


if __name__ == '__main__':
    unittest.main()
