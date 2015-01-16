#!/usr/bin/env python
# Copyright (C) 2015 Caleb Levy - All Rights Reserved.
#
# The terms of use, license and copyright information for the code and ideas
# contained herein are described in the LICENSE file included with this
# project. For more information please contact me at caleb.levy@berkeley.edu.
"""
A collection of utilities returning certain information about and kinds of
images of sets under functions: preimages, cardinalities of iterate images,
cycle decompositions and limitsets.

These should all be made into methods. We will have:
    - f.cycles()
    - f.preimage(I)
"""
from nestops import flatten
from iteration import endofunctions

from random import randrange
from collections import deque
import unittest



randfunc = lambda n: [randrange(n) for I in range(n)]


def preimage(f):
    """
    Given an endofunction f defined on S=range(len(f)), returns the preimage of
    f. If g=preimage(f), we have

        g[y]=[x for x in S if f[x]==y],

    or mathematically:

        f^-1(y)={x in S: f(x)=y}.

    Note the particularly close correspondence between python's list
    comprehensions and mathematical set-builder notation.
    """
    S = range(len(f))
    preim = []
    for y in S:
        preim.append([x for x in S if y == f[x]])
    return preim


def imagepath(f):
    """
    Give it a list so that all([I in range(len(f)) for I in f]) and this
    program spits out the image path of f.
    """
    n = len(f)
    cardinalities = [len(set(f))]
    f_orig = f[:]
    card_prev = n
    for it in range(1, n-1):
        f = [f_orig[x] for x in f]
        card = len(set(f))
        cardinalities.append(len(set(f)))
        if card == card_prev:
            cardinalities.extend([card]*(n-2-it))
            break
        card_prev = card
    return cardinalities


def funccycles(f):
    """
    Given an endofunction f, return its cycle decomposition.
    """
    N = len(f)
    if N == 1:
        yield [0]
        return
    cycles = []
    cycle_els = []
    for x in range(N):
        path = [x]
        for it in range(N):
            x = f[x]
            path.append(x)
        I = N-1
        while I >= 0 and path[I] != path[-1]:
            I -= 1
        if path[-1] not in cycle_els:
            yield path[I+1:]
            cycle_els.extend(path[I+1:])

limitset = lambda f: flatten(funccycles(f))


def attached_treenodes(f):
    """
    Returns subsets of the preimages of each element which are not in cycles.
    """
    descendents = preimage(f)
    limset = limitset(f)
    for preim in descendents:
        for x in limset:
            if x in preim:
                preim.remove(x)
    return descendents


class ImagepathTest(unittest.TestCase):

    def testImagepath(self):
        """Check various special and degenerate cases, with right index"""
        self.assertEqual([1], imagepath([0]))
        self.assertEqual([1], imagepath([0, 0]))
        self.assertEqual([1], imagepath([1, 1]))
        self.assertEqual([2], imagepath([0, 1]))
        self.assertEqual([2], imagepath([1, 0]))
        node_count = [2, 3, 5, 15]
        for n in node_count:
            tower = [0] + list(range(n-1))
            cycle = [n-1] + list(range(n-1))
            fixed = list(range(n))
            degen = [0]*n
            self.assertEqual(list(range(n)[:0:-1]), imagepath(tower))
            self.assertEqual([n]*(n-1), imagepath(cycle))
            self.assertEqual([n]*(n-1), imagepath(fixed))
            self.assertEqual([1]*(n-1), imagepath(degen))


class CycleTests(unittest.TestCase):
    funcs = [
        [1, 0],
        [9, 5, 7, 6, 2, 0, 9, 5, 7, 6, 2],
        [7, 2, 2, 3, 4, 3, 9, 2, 2, 10, 10, 11, 12, 5]
    ]
    # Use magic number for python3 compatibility
    funcs += list([randfunc(20) for I in range(100)])
    funcs += list(endofunctions(1))
    funcs += list(endofunctions(3)) + list(endofunctions(4))

    def testCyclesAreCyclic(self):
        for f in self.funcs:
            for cycle in funccycles(f):
                for ind, el in enumerate(cycle):
                    self.assertEqual(cycle[(ind+1) % len(cycle)], f[el])

    def testCyclesAreUnique(self):
        for f in self.funcs:
            cycleset = [tuple(cycle) for cycle in funccycles(f)]
            self.assertEqual(len(cycleset), len(set(cycleset)))

    def testCyclesAreComplete(self):
        for f in self.funcs:
            cycle_size = len(flatten(funccycles(f)))
            self.assertEqual(imagepath(f)[-1], cycle_size)

    def testTreenodesAreNotCyclic(self):
        for f in self.funcs:
            lim = limitset(f)
            descendents = attached_treenodes(f)
            for preim in descendents:
                for x in preim:
                    self.assertTrue(x not in lim)


if __name__ == '__main__':
    unittest.main()
