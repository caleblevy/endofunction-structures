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

from PADS.IntegerPartitions import partitions

import subsequences
import multiset
import iterate
import nestops
import factorization
import conjugates


def treeroot(treefunc):
    """Returns the root of an endofunction whose structure is a rooted tree."""
    return [x for x in range(len(treefunc)) if treefunc[x] == x][0]

class RootedTree(object):
    """Represents an unlabelled rooted tree."""

    def __init__(self, level_sequence):
        self.level_sequence = tuple(level_sequence)
        self.root_level = level_sequence[0]
        self.n = len(level_sequence)

    def __repr__(self):
        return "RootedTree("+str(list(self.level_sequence))+')'

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.level_sequence == other.level_sequence
        else:
            return False

    def __hash__(self):
        return hash(tuple(self.level_sequence))

    def __len__(self):
        return self.n

    def branches(self):
        """Return each major subbranch of a tree (even chopped)"""
        rootcheck = lambda node: node == self.root_level + 1
        return subsequences.startswith(self.level_sequence[1:], rootcheck)

    def subtrees(self):
        for branch in self.branches():
            yield self.__class__([node-1 for node in branch])

    def chop(self):
        """Generates the canonical subtrees of the input tree's root node."""
        return tuple(subtree for subtree in self.subtrees())

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
        return deg*multiset.mset_degeneracy(self.chop())

    def func_form(self, permutation=None):
        """
        Return an endofunction whose structure corresponds to the rooted tree.
        The root is 0 by default, but can be permuted according a specified
        permutation.
        """
        if permutation is None:
            permutation = range(self.n)
        height = max(self.level_sequence)
        func = [0]*self.n
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
        return func

    def bracket_form(self):
        """
        Return a representation the rooted tree via nested lists. This method
        is a novelty item, and shouldn't be used for anything practical.
        """
        treefunc = self.func_form()
        preim = iterate.attached_treenodes(treefunc)
        root = treeroot(treefunc)
        brackets = preim[root]
        indset = [[x] for x in range(len(brackets))]
        while indset:
            nextinds = []
            for ind in indset:
                # For each ind, get the corresponding node
                el = nestops.get_nested_el(brackets, ind)
                # Collect the indicies of all nodes connected to el
                nextinds.extend([ind+[I] for I in range(len(preim[el]))])
                # Set el to its preimage until only empty lists are left.
                nestops.change_nested_el(brackets, ind, preim[el])
            indset = nextinds
        return brackets


    def _istree(self):
        pass

    @classmethod
    def from_treefunc(cls, func):
        pass


class RootedTrees(object):
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
        yield tree
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
                yield tree

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

        NOTE: For n >= 47, len(RootedTrees(n)) is greater than C long, and thus
        gives rise to an index overflow error. Use self._calculate_len instead.
        """
        if self._memoized_len is None:
            self._memoized_len = self._calculate_len()
        return self._memoized_len


def rooted_trees(n):
    """
    This function serves as a placeholder until I update the function call name
    from rooted_trees to RootedTrees in other modules.
    """
    return RootedTrees(n)

tree_tuples = lambda n: (tuple(tree) for tree in rooted_trees(n))


def rooted_treecount(n):
    """
    This function serves as a placeholder until I update the function call name
    from rooted_treecount_upto to len(RootedTrees(n) in other modules.
    """
    return len(RootedTrees(n))

rooted_treecount = lambda n: len(RootedTrees(n))


def partition_forests(partition):
    """
    Generates the forests formed from rooted trees with sizes specified by
    partitions
    """
    y, d = multiset.split_set(partition)
    l = len(y)
    trees = [tree_tuples(I) for I in y]

    preseed = [itertools.combinations_with_replacement(trees[I], d[I])
               for I in range(l)]

    seeds = [list(seed) for seed in preseed]
    for forest in itertools.product(*seeds):
        yield tuple(nestops.flatten(forest))


def forests_complex(n):
    """
    For a given partition of N elements, we can make combinations of trees on
    each of the node groups of that partition. Iterating over all partitions
    gives us all collections of rooted trees on N nodes.
    """
    if n == 0:
        return
    for partition in partitions(n):
        for forest in partition_forests(partition):
            yield forest


def branches(tree):
    """Return each major subbranch of a tree (even chopped)"""
    return subsequences.startswith(tree[1:], lambda node: node == tree[0]+1)


def subtrees(tree):
    for branch in branches(tree):
        yield [node-1 for node in branch]


def chop(tree):
    """Generates the canonical subtrees of the input tree's root node."""
    return tuple(tuple(subtree) for subtree in subtrees(tree))


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
    for tree in rooted_trees(N+1):
        yield chop(tree)

forests = forests_simple


def tree_degeneracy(tree): # Wrapper for RootedTree method
    return RootedTree(tree).degeneracy()


def tree_to_func(tree, permutation=None): # Wrapper for RootedTree method
    return RootedTree(tree).func_form(permutation)

def tree_to_brackets(tree): # Wrapper for RootedTree method.
    return RootedTree(tree).bracket_form()


def canonical_treeorder(tree):
    """
    Given a noncanonical (non lexicographically maximal) level sequence, return
    the canonical representation of the equivalent tree.
    """
    if not list(branches(tree)):
        return tree
    branch_list = []
    for branch in branches(tree):
        branch_list.append(canonical_treeorder(branch))
    return [tree[0]]+nestops.flatten(sorted(branch_list, reverse=True))


def _attached_subtree(node, level, treenodes):
    """
    Recursive portion of the subtree algorithm. Returns [level] of the node
    plus level path of all attached subnodes, hence the itero-recursion.
    """
    leveltree = [level]
    for x in treenodes[node]:
        leveltree.extend(_attached_subtree(x, level+1, treenodes))
    return leveltree


def attached_subtree(f, node):
    """
    Given an endofunction f and node in range(len(f)), returns the levelpath
    form of the rooted tree attached to element node.
    """
    treenodes = iterate.attached_treenodes(f)
    leveltree = [1]
    if not treenodes[node]:
        return leveltree
    level = 2
    for x in treenodes[node]:
        leveltree += _attached_subtree(x, level, treenodes)
    return canonical_treeorder(leveltree)


def treefunc_to_tree(treefunc):
    n = len(treefunc)
    root = [x for x in range(n) if treefunc[x] == x][0]
    return attached_subtree(treefunc, root)


class TreeTest(unittest.TestCase):
    A000081 = [1, 1, 2, 4, 9, 20, 48, 115, 286]

    def testTrees(self):
        """OEIS A000081: number of unlabelled rooted trees on N nodes."""
        for n, count in enumerate(self.A000081):
            self.assertEqual(count, len(list(rooted_trees(n+1))))
            self.assertEqual(count, rooted_treecount(n+1))

    def testForests(self):
        """Check len(forests(N))==A000081(N+1)"""
        for n, count in enumerate(self.A000081[1:]):
            self.assertEqual(count, len(set(forests_simple(n+1))))
            self.assertEqual(count, len(set(forests_complex(n+1))))

    def testDegeneracy(self):
        """OEIS A000169: n**(n-1) == number of rooted trees on n nodes."""
        # self.assertEqual(1, tree_degeneracy(tuple()))
        for n in range(1, len(self.A000081)):
            labelled_treecount = 0
            for tree in rooted_trees(n):
                labelled_treecount += math.factorial(n)//tree_degeneracy(tree)
            self.assertEqual(n**(n-1), labelled_treecount)

    def testTreeToFunc(self):
        """Make sure treetofunc correctly represents trees as endofunctions"""
        tree = [1, 2, 3, 4, 4, 4, 3, 4, 4, 2, 3, 3, 2, 3]
        func = [0, 0, 1, 2, 2, 2, 1, 6, 6, 0, 9, 9, 0, 12]
        self.assertSequenceEqual(func, tree_to_func(tree))

    def testTreeform(self):
        """Test the bracket representation of these rooted trees."""
        trees = [
            [1, 2, 3, 4, 5, 6, 4, 2, 3, 4],
            [1, 2, 3, 4, 5, 6, 4, 2, 3, 3],
            [1, 2, 3, 4, 5, 5, 5, 5, 5, 2],
        ]
        nestedforms = (
            [[[[[[]]], []]], [[[]]]],
            [[[[[[]]], []]], [[], []]],
            [[[[[], [], [], [], []]]], []]
        )
        for tree, nest in zip(trees, nestedforms):
            self.assertSequenceEqual(nest, tree_to_brackets(tree))

    def testTreefuncToTree(self):
        """Tests attached treenodes and canonical_treeorder in one go."""
        for n in range(1, len(self.A000081)+1):
            for tree in rooted_trees(n):
                treefunc = tree_to_func(tree)
                for _ in range(10):
                    rtreefunc = conjugates.randconj(treefunc)
                    self.assertSequenceEqual(tree, treefunc_to_tree(rtreefunc))


if __name__ == '__main__':
    unittest.main()
