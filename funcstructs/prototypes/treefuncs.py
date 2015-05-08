"""Honing of lazy tree function evaluation with a sane interface.

Caleb Levy, 2015.
"""

from __future__ import print_function
from collections import defaultdict


@classmethod
def from_func(cls, func, root=None):
    """Return the level sequence of the rooted tree formed from the graph of
    all noncyclic nodes whose iteration paths pass through node. If no node is
    specified, and the function does not have a unique cyclic element, a
    ValueError is raised."""
    if root is None:
        root = next(iter(func.limitset))
        if len(func.limitset) != 1:
            raise ValueError("Function structure is not a rooted tree")
    return cls(levels_from_preim(func.acyclic_ancestors, root))


def levels_from_preim(graph, root=0, keys=None):
    """Return the level sequence of the ordered tree formed such that graph[x]
    are the nodes attached to x."""
    preim = graph
    if keys is not None:
        preim = defaultdict(lambda node: sorted(graph[node], key=keys))
    node_stack = [root]
    level = 0
    node_levels = {root: level}
    while node_stack:
        x = node_stack.pop()
        level = node_levels[x]
        yield level
        level += 1
        for y in preim[x]:
            node_stack.append(y)
            # Need to compute even for dominant tree, since levels will change
            node_levels[y] = level


def funclevels_iterator(levels):
    """Lazily generate the function of a level tree and each node's level"""
    levels = iter(levels)
    root = previous_level = next(levels)
    f = node = 0
    yield node, previous_level, f  # node, height, and what it's mapped to
    grafting_point = {0: 0}
    for node, level in enumerate(levels, start=1):
        if level > previous_level:
            f = grafting_point[previous_level-root]
            previous_level += 1
        else:
            f = grafting_point[level-root-1]
            previous_level = level
        yield node, level, f
        grafting_point[level-root] = node


def tree_properties(levels):
    """Return an endofunction corresponding to a sequence of levels"""
    func = []
    height_groups = defaultdict(list)
    preim = defaultdict(set)
    for n, l, f in funclevels_iterator(levels):
        func.append(f)
        preim[f].add(n)
        height_groups[l].append(n)
    preim[0].remove(0)
    return func, preim, height_groups


t = iter([0, 1, 2, 2, 3, 3, 3, 4, 5, 5, 4, 3, 3, 2, 1, 2])
print(tree_properties(t))
