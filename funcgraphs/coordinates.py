# Copyright (C) 2015 Caleb Levy - All Rights Reserved.
#
# The terms of use, license and copyright information for the code and ideas
# contained herein are described in the LICENSE file included with this
# project. For more information please contact me at caleb.levy@berkeley.edu.

"""Module for representing and manipulating 2D cartesian coordinates both in
isolation and in groups."""

import numbers
import unittest

import numpy as np
import matplotlib.pyplot as plt

__all__ = ["Point", "Coordinates"]


class LocationSpecifier2D(object):
    """Abstract coordinates. Invoked either as a point or a point cloud. """

    def __init__(self, x, y=None):
        # Conceptually, Location2D should be an abstract base class. However,
        # without some ugly hacks or third party libraries, there is no python
        # 2 and 3 compatible syntax for specifying a metaclass, so we mock
        # ABCMeta by raising an error at instantiation.
        raise NotImplementedError("Cannot call LocationSpecifier2D directly.")

    @classmethod
    def from_polar(cls, r, theta):
        return cls(r*np.exp(1j*theta))

    @property
    def z(self):
        """Return the locations as points on the complex plane"""
        return self._coord

    def __abs__(self):
        return np.abs(self.z)

    @property
    def x(self):
        """Return x components of the cartesian representations"""
        return self.z.real

    @property
    def y(self):
        """Return the y components of cartesian representations"""
        return self.z.imag

    @property
    def r(self):
        """Return radial components of the polar representation"""
        return abs(self)

    @property
    def theta(self):
        """Return the angular component of the polar representation"""
        return np.arctan2(self.y, self.x)

    def __add__(self, other):
        """Change to coordinates in which old origin is now at other in new"""
        return self.__class__(self.z + Point(other).z)

    def __neg__(self):
        """Reflection about the origin"""
        return self.__class__(-self.z)

    def __sub__(self, other):
        """Change to coordinates such that new origin is at other in the old"""
        return -(-self + other)

    def __rmul__(self, other):
        """Scale self by real value other. """
        if isinstance(other, numbers.Real):
            return self.__class__(other*self.z)
        raise TypeError("Cannot multiply coordinates by %s" % str(type(other)))

    def __div__(self, other):
        """inverse of mul"""
        return (1./other) * self

    __truediv__ = __div__

    def rotate(self, angle, origin=0):
        """Rotate the locations by angle about point p, default is origin"""
        coords = self - origin
        r, theta = coords.r, coords.theta
        self._coord = (self.from_polar(r, theta + angle) + origin).z


def check_components_are_real(x, y):
    """Check that both x and y are real numbers, if not raise error"""
    isreal = lambda ob: isinstance(ob, numbers.Real)
    if not(isreal(x) and isreal(y)):
        raise TypeError(
            ("Both coordinates must be real numbers, "
             "received %s, %s") % (type(x).__name__, type(y).__name__)
        )


class Point(LocationSpecifier2D):
    """A basic cartesian point. Internally represented as a complex number
    (i.e. a point in the complex plane)."""

    def __init__(self, x, y=None):
        """All of the following inputs to point are equivalent:
            Point(1, 2)
            Point((1, 2))
            Point(1+2j)
            Point(Point(1, 2))
        Any other input will raise a value error."""
        if y is not None:
            check_components_are_real(x, y)
            z = x + 1j*y
        elif hasattr(x, '__iter__'):
            check_components_are_real(x[0], x[1])
            if len(x) != 2:
                raise ValueError("More than one coordinate specified.")
            z = x[0] + 1j*x[1]
        else:
            z = complex(x)  # Explicitly cast to complex (e.g. if ints)
        self._coord = z

    def __mul__(self, other):
        """Dot product with other vector."""
        other = Point(other)
        return self.x * other.x + self.y * other.y

    def __repr__(self):
        return type(self).__name__+'(%s, %s)' % (str(self.x), str(self.y))

    def __eq__(self, other):
        if isinstance(other, type(self)):
            return self.z == other.z
        return False

    def __ne__(self, other):
        return not self == other

    def __complex__(self):
        return self.z


def check_coords_are_real(x, y):
    """Check that x and y are real valued arrays"""
    array_is_real = lambda arr: issubclass(arr.dtype.type, numbers.Real)
    if not(array_is_real(x) and array_is_real(y)):
        raise TypeError(
            ("Both coordinates must be real valued, received"
             " %s, %s" % (x.dtype.type.__name__, y.dtype.type.__name__))
        )


class Coordinates(LocationSpecifier2D):
    """A set of points internally represented by a numpy array."""

    def __init__(self, x, y=None):
        """All of the following inputs to point are equivalent:
            Coordinates([Point(1, 2), Point(3, 4), Point(5, 6)])
            Coordinates([1, 3, 5], [2, 4, 6])
            Coordinates([1+2j, 3+4j, 5+6j])
        Any other input will raise a value error."""
        x = np.array(x)
        if x.ndim != 1:
            raise TypeError("Input must be flat iterable location collection")
        if y is not None:
            y = np.array(y)
            check_coords_are_real(x, y)
            if x.shape != y.shape:
                raise ValueError("Inputs must be equal length")
            z = x + 1j*y
        else:
            z = x.astype(complex)
        self._coord = z

    def __repr__(self):
        return type(self).__name__+'(%s)' % repr(list(self))

    def __len__(self):
        """Number of points in the set"""
        return len(self.z)

    def __iter__(self):
        """Enumerate all points in z."""
        for p in self.z:
            yield Point(p)

    def __getitem__(self, key):
        """Return the nth point in the cloud"""
        if isinstance(key, int):
            return Point(self.z[key])
        return Coordinates(self.z[key])

    def plot(self, *args, **kwargs):
        """Draw connected sequence of points"""
        if kwargs.get('ax', None) is not None:
            ax = kwargs['ax']
        else:
            ax = plt.gca()
        kwargs.pop('ax', None)
        ax.plot(self.x, self.y, *args, **kwargs)


class Location2DTests(unittest.TestCase):

    def test_polar_coordinates(self):
        """Test going back and forth from cartesian to polar."""
        # From polar to cartesian
        p1 = Point(1, 2)
        rp1 = Point.from_polar(p1.r, p1.theta)
        self.assertAlmostEqual(p1, rp1)
        # From Cartesian to polar
        p2 = Point(-1, 1)
        self.assertAlmostEqual(np.sqrt(2), p2.r)
        self.assertAlmostEqual(3*np.pi/4, p2.theta)
        # Test on arrays
        x = np.linspace(0, 1, 10)
        c = Coordinates(x, x)
        for p in c[1:]:
            self.assertAlmostEqual(np.pi/4, p.theta)

    def test_from_polar(self):
        """Test forming a vector from polar coordinates behaves correctly."""
        # Test the origin
        o = Point(0, 0)
        p = Point.from_polar(0, 0)
        self.assertAlmostEqual(p, o)
        # Test a vertical line
        h = Point.from_polar(2, np.pi/2)
        self.assertAlmostEqual(Point(0, 2), h)
        # Test periodic in 2*pi
        k1 = Point.from_polar(2, -3)
        k2 = Point.from_polar(2, -3+2*np.pi)
        self.assertAlmostEqual(k1, k2)
        # test coordinate array
        x = np.linspace(0, 1, 10)
        par = Coordinates(x, x**2)
        np.testing.assert_allclose(
            par.z,
            Coordinates.from_polar(par.r, par.theta).z
        )
        self.assertAlmostEqual(par.theta[-1], np.pi/4)

    def test_negation(self):
        """Test that negation mirrors points about y=-x"""
        self.assertAlmostEqual(Point(-1, -2), -Point(1, 2))
        # test on arrays
        np.testing.assert_allclose(
            Coordinates([Point(-1, -2), Point(3, -4), Point(4, -5)]).z,
            -Coordinates([Point(1, 2), Point(-3, 4), Point(-4, 5)]).z
        )

    def test_rotation(self):
        """Test rotation and unrotation of a point"""
        # Test rotation maintains object identity
        a = Point(1, 2)
        ai = a
        a.rotate(3)
        a.rotate(-3)
        self.assertIs(ai, a)
        self.assertAlmostEqual(Point(1, 2), a)
        a.rotate(np.pi)
        self.assertAlmostEqual(-Point(1, 2), a)
        # Test dot product with perpendicular is zero
        b = Point(3, -4)
        br = Point(b)
        br.rotate(np.pi/2)
        self.assertAlmostEqual(0, b * br)
        # Test rotating coordinates
        x = np.linspace(0, 1, 10)
        par = Coordinates(x, x**2)
        par.rotate(np.pi/4)
        self.assertAlmostEqual(np.pi/2, par[-1].theta)


class PointTests(unittest.TestCase):

    def test_init(self):
        """Ensure equivalence of various ways to initialize a point."""
        points = [Point(1, 2), Point((1, 2)), Point(1+2j), Point(Point(1, 2))]
        for p in points:
            for q in points:
                self.assertAlmostEqual(p, q)
        erroneous_args = [
            {'x': 1, 'y': 2j},  # y is complex
            {'x': 1j, 'y': 2},  # x is complex with sepcified y
            {'x': [1], 'y': [2]},  # x and y both lists
            {'x': [1]},  # Not enough coordinates
            {'x': [1, 2, 3]},  # Too many coordinates
            {'x': [1, 2j]},  # Complex values in coordinate tuple
            {'x': Point(1, 2), 'y': Point(3, 4)},  # Two complex valued points
            {'x': np.array(1)}  # 0-dim array
        ]
        for components in erroneous_args:
            with self.assertRaises(Exception):
                Point(**components)

    def test_repr(self):
        p1 = Point(1., 2.)
        p2 = Point(-7, 56)
        self.assertAlmostEqual(p1, eval(repr(p1)))
        self.assertAlmostEqual(p2, eval(repr(p2)))

    def test_dot_product(self):
        """Test values for the dot product of points"""
        p1 = Point((1, 2))
        p2 = Point((3, 4))
        # Test commutativity
        self.assertEqual(11, p1 * p2)
        self.assertEqual(11, p2 * p1)
        p3 = Point(-2, 1)
        self.assertEqual(0., p1 * p3)
        self.assertEqual(0., p3 * p1)


class CoordinateTests(unittest.TestCase):

    def test_init(self):
        coord_sets = [
            Coordinates([Point(1, 2), Point(3, 4), Point(5, 6)]),  # point list
            Coordinates([1, 3, 5], [2, 4, 6]),  # from x and y components
            Coordinates([1+2j, 3+4j, 5+6j])  # from locations on complex pane
        ]
        for c in coord_sets:
            for d in coord_sets:
                np.testing.assert_allclose(c.z, d.z)
        erroneous_args = [
            {'x': [1, 2, Point(1)], 'y': [1, 2, 3]},  # complex x component
            {'x': [1, 2, 1], 'y': [1, 2, 3j]},  # complex y component
            {'x': [1, 3, 5], 'y': [1, 2j]},  # more x components than y
            {'x': [1, 2], 'y': [1, 2, 3]},  # more y components
            {'x': [1, 2, [3]]},  # iterable points
            {'x': 1, 'y': 2},  # uniterable coordinates
            {'x': [(1, 2), (3, 4), (5, 6)]},  # tuple components
        ]
        for components in erroneous_args:
            with self.assertRaises(Exception):
                Coordinates(**components)

    def test_repr(self):
        coords1 = Coordinates([1, 2, 3], [4, 5, 6])
        coords2 = Coordinates(range(10), np.arange(10)**2)
        np.testing.assert_allclose(coords1.z, eval(repr(coords1)).z)
        np.testing.assert_allclose(coords2.z, eval(repr(coords2)).z)

    def test_container_methods(self):
        """Test __iter__, __len__ and __getitem__ methods"""
        coords = Coordinates(range(10), np.arange(10)**2)
        for i, p in enumerate(coords):
            self.assertAlmostEqual(Point(i, i**2), p)
            self.assertAlmostEqual(p, coords[i])
        self.assertEqual(10, len(coords))
        np.testing.assert_allclose(
            coords.z,
            Coordinates.from_polar(coords.r, coords.theta).z
        )


if __name__ == '__main__':
    unittest.main()
