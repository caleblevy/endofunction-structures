#!/usr/bin/env python
# Copyright (C) 2014-2015 Caleb Levy - All Rights Reserved.
#
# The terms of use, license and copyright information for the code and ideas
# contained herein are described in the LICENSE file included with this
# project. For more information please contact me at caleb.levy@berkeley.edu.

"""
A rooted tree is a connected digraph with a single cycle such that every node's
outdegree and every cycle's length is exactly one. Alternatively, it is a tree
with a designated "root" node, where every path ends with the root. They are
equivalent to filesystems consisting entirely of folders with no symbolic
links. An unlabelled rooted tree is the equivalence class of a given directory
where folders in each subdirectory may be rearranged in any desired order
(alphabetical, reverse-alphabetical, date added, or any other permutation). A
forest is any collection of rooted trees.

Any endofunction structure may be represented as a forest of trees, grouped
together in multisets corresponding to cycle decompositions of the final set
(the subset of its domain on which it is invertible). The orderings of the
trees in the multisets correspond to necklaces whose beads are the trees
themselves.
"""


import math
import unittest
import itertools
import functools

from PADS.IntegerPartitions import partitions

import subsequences
import multiset
import nestops
import factorization
import endofunctions

class RootedTree(object):

    def __init__(self, subtrees=None):
        # there is no root; this is totally structureless.
        if subtrees is None:
            self.subtrees = multiset.Multiset()
        subtrees = multiset.Multiset(subtrees)
        for subtree in subtrees.unique_elements():
            if not isinstance(subtree, RootedTree):
                raise ValueError("Subtrees must be rooted trees")
        self.subtrees = subtrees

    def __hash__(self):
        return hash(self.subtrees)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.subtrees == other.subtrees
        return False

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return "RootedTree(%s)"%repr(self)

    def __repr__(self):
        if not self.subtrees:
            return '{}'
        return str(self.subtrees)

@functools.total_ordering
class OrderedTree(object):
    """Represents an unlabelled rooted tree."""

    def __init__(self, level_sequence):
        self.level_sequence = tuple(level_sequence)
        self.n = len(level_sequence)

    def __repr__(self):
        return self.__class__.__name__ + "("+str(list(self.level_sequence))+')'

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.level_sequence == other.level_sequence
        else:
            return False

    def __ne__(self, other):
        return not (self == other)

    def __le__(self, other):
        if isinstance(other, self.__class__):
            return self.level_sequence <= other.level_sequence
        else:
            raise ValueError("Cannot compare tree with type %s"%type(other))

    def __hash__(self):
        return hash(self.level_sequence)

    def __len__(self):
        return self.n

    def __iter__(self):
        return iter(self.level_sequence)

    def __bool__(self):
        return bool(self.level_sequence)

    __nonzero__ = __bool__

    def branches(self):
        """Return each major subbranch of a tree (even chopped)"""
        if not self:
            return
        isroot = lambda node: node == self.level_sequence[0] + 1
        for branch in subsequences.startswith(self.level_sequence[1:], isroot):
            yield OrderedTree(branch)

    def subtrees(self):
        for branch in self.branches():
            yield OrderedTree([node-1 for node in branch])

    def chop(self):
        """Generates the canonical subtrees of the input tree's root node."""
        return multiset.Multiset(subtree for subtree in self.subtrees())

    def degeneracy(self, call_level=1):
        """
        To calculate the degeneracy of a collection of subtrees you start with
        the lowest branches and then work upwards. If a group of identical
        subbranches are connected to the same node, we multiply the degeneracy
        of the tree by the factorial of the multiplicity of these subbranches
        to account for their distinct orderings. The same principal applies to
        subtrees.

        TODO: A writeup of this with diagrams will be in the notes.
        """
        if not self.chop():
            return 1
        deg = 1
        for subtree in self.chop():
            deg *= subtree.degeneracy()
        return deg*self.chop().degeneracy()

    def func_form(self, permutation=None):
        """
        Return an endofunction whose structure corresponds to the rooted tree.
        The root is 0 by default, but can be permuted according a specified
        permutation.
        """
        if permutation is None:
            permutation = range(len(self))
        height = max(self)
        func = [0]*len(self)
        func[0] = permutation[0]
        height_prev = 1
        # Most recent node found at height h. Where to graft the next node to.
        grafting_point = [0]*height
        for node, height in enumerate(self.level_sequence[1:]):
            if height > height_prev:
                func[node+1] = permutation[grafting_point[height_prev-1]]
                height_prev += 1
            else:
                func[node+1] = permutation[grafting_point[height-2]]
                height_prev = height
            grafting_point[height-1] = node+1
        return endofunctions.Endofunction(func)

    def bracket_form(self):
        """
        Return a representation the rooted tree via nested lists. This method
        is a novelty item, and shouldn't be used for anything practical.
        """
        if not self:
            return []
        return [subtree.bracket_form() for subtree in self.subtrees()]

    def unordered(self):
        if not self:
            return RootedTree()
        return RootedTree(subtree.unordered() for subtree in self.subtrees())

    def dominant_level_sequence(self):
        """
        Return the lexicographically dominant rooted tree corresponding to self.
        """
        if not self.branches():
            return self.level_sequence
        branch_list = []
        for branch in self.branches():
            branch_list.append(branch.dominant_level_sequence())
        branch_list.sort(reverse=True)
        return [self.level_sequence[0]] + nestops.flatten(branch_list)

    def canonical_form(self):
        """Return a dominant tree type."""
        return OrderedTree(self.dominant_level_sequence())


def treefunc_to_dominant_tree(treefunc):
    """Test if a function has a tree structure and if so return it."""
    cycles = list(treefunc.cycles)
    if len(cycles) != 1 or len(cycles[0]) != 1:
        raise ValueError("Function structure is not a rooted tree.")
    root = cycles[0][0]
    return OrderedTree(treefunc.attached_level_sequence(root)).canonical_form()

a = RootedTree()
b = OrderedTree([1,2,3,4,5,4,5,5,2,3,2,3,4,4,5,6])
print b.unordered()
print OrderedTree(range(1,5)).unordered()
print OrderedTree([1,2,3,4,5,4,5,5,2,3,4,5,5,4,5]).unordered()


class OrderedTrees(object):
    """Represents the class of unlabelled rooted trees on n nodes."""

    def __init__(self, node_count):
        self.n = node_count
        self._memoized_len = None

    def __iter__(self):
        """
        Takes an integer N as input and outputs a generator object enumerating
        all isomorphic unlabeled rooted trees on N nodes.

        The basic idea of the algorithm is to represent a tree by its level
        sequence: list each vertice's height above the root, where vertex v+1
        is connected either to vertex v or the previous node at some lower
        level.

        Choosing the lexicographically greatest level sequence gives a
        canonical representation for each rooted tree. We start with the
        tallest rooted tree given by T=range(1,N+1) and then go downward,
        lexicographically, until we are flat so that T=[1]+[2]*(N-1).

        Algorithm and description provided in:
            T. Beyer and S. M. Hedetniemi. "Constant time generation of rooted
            trees." Siam Journal of Computation, Vol. 9, No. 4. November 1980.
        """
        tree = [I+1 for I in range(self.n)]
        yield OrderedTree(tree)
        if self.n > 2:
            while tree[1] != tree[2]:
                p = self.n-1
                while tree[p] == tree[1]:
                    p -= 1
                q = p-1
                while tree[q] >= tree[p]:
                    q -= 1
                for I in range(p, self.n):
                    tree[I] = tree[I-(p-q)]
                yield OrderedTree(tree)

    def _calculate_len(self):
        """
        Returns the number of rooted tree structures on n nodes. Algorithm
        featured without derivation in
            Finch, S. R. "Otter's Tree Enumeration Constants." Section 5.6 in
            "Mathematical Constants", Cambridge, England: Cambridge University
            Press, pp. 295-316, 2003.
        """
        T = [0, 1] + [0]*(self.n - 1)
        for n in range(2, self.n + 1):
            for i in range(1, self.n):
                s = 0
                for d in factorization.divisors(i):
                    s += T[d]*d
                s *= T[n-i]
                T[n] += s
            T[n] //= n-1
        return T[-1]

    def __len__(self):
        """
        Hook for python len function.

        NOTE: For n >= 47, len(OrderedTrees(n)) is greater than C long, and thus
        gives rise to an index overflow error. Use self._calculate_len instead.
        """
        if self._memoized_len is None:
            self._memoized_len = self._calculate_len()
        return self._memoized_len


def forests_simple(N):
    """
    Any rooted tree on N+1 nodes can be identically described by a collection
    of rooted trees on N nodes, grafted together at a single root.

    To enumerate all collections of rooted trees on N nodes, we reverse the
    principle and enumerate all rooted trees on N+1 nodes, chopping them at the
    base. Much simpler than finding all trees corresponding to a partition.
    """
    if N == 0:
        return
    for tree in OrderedTrees(N+1):
        yield tree.chop()

forests = forests_simple


class TreeTest(unittest.TestCase):
    A000081 = [1, 1, 2, 4, 9, 20, 48, 115, 286]

    def testTreeCounts(self):
        """OEIS A000081: number of unlabelled rooted trees on N nodes."""
        for n, count in enumerate(self.A000081):
            self.assertEqual(count, len(list(OrderedTrees(n+1))))
            self.assertEqual(count, len(OrderedTrees(n+1)))

    def testForestCounts(self):
        """Check len(forests(N))==A000081(N+1)"""
        for n, count in enumerate(self.A000081[1:]):
            self.assertEqual(count, len(set(forests_simple(n+1))))

    def testTreeDegeneracy(self):
        """OEIS A000169: n**(n-1) == number of rooted trees on n nodes."""
        # self.assertEqual(1, tree_degeneracy(tuple()))
        for n in range(1, len(self.A000081)):
            labelled_treecount = 0
            for tree in OrderedTrees(n):
                labelled_treecount += math.factorial(n)//tree.degeneracy()
            self.assertEqual(n**(n-1), labelled_treecount)

        """Prove ordering of the subtrees does not matter"""
        lev = [1,2,3,4,2,3,4,5,3,4,3,4,4,3,4,5,2,2,3]
        a = OrderedTree(lev)
        b = OrderedTree(lev).canonical_form()
        self.assertTrue(a != b)
        self.assertTrue(a.degeneracy() == b.degeneracy())

    def testTreeFuncForm(self):
        """Make sure treetofunc correctly represents trees as endofunctions"""
        tree = OrderedTree([1, 2, 3, 4, 4, 4, 3, 4, 4, 2, 3, 3, 2, 3])
        func = endofunctions.Endofunction([0, 0, 1, 2, 2, 2, 1, 6, 6, 0, 9, 9, 0, 12])
        self.assertEqual(func, tree.func_form())

    def testTreeBracketForm(self):
        """Test the bracket representation of these rooted trees."""
        trees = [
            OrderedTree([1, 2, 3, 4, 5, 6, 4, 2, 3, 4]),
            OrderedTree([1, 2, 3, 4, 5, 6, 4, 2, 3, 3]),
            OrderedTree([1, 2, 3, 4, 5, 5, 5, 5, 5, 2]),
        ]
        nestedforms = (
            [[[[[[]]], []]], [[[]]]],
            [[[[[[]]], []]], [[], []]],
            [[[[[], [], [], [], []]]], []]
        )
        for tree, nest in zip(trees, nestedforms):
            self.assertSequenceEqual(nest, tree.bracket_form())

    def testTreefuncToTree(self):
        """Tests attached treenodes and canonical_treeorder in one go."""
        for n in range(1, len(self.A000081)+1):
            for tree in OrderedTrees(n):
                treefunc = tree.func_form()
                for _ in range(10):
                    rtreefunc = treefunc.randconj()
                    self.assertEqual(tree, treefunc_to_dominant_tree(rtreefunc))


if __name__ == '__main__':
    unittest.main()
