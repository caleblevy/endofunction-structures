"""Data structures for representing mappings between sets.

Caleb Levy, 2015.
"""

import itertools
import random
from collections import defaultdict
from math import factorial

from funcstructs import bases
from funcstructs.utils.misc import cached_property, flatten


def _result_functype(f, g):
    """Coerce func types of f and g into the proper type. Rules are:
        1) If both types are the same, so is their result
        2) Function has highest priority
        3) SymmetricFunction has lowest priority
        4) Bijection and Endofunction result in Function
    """
    functypes = {type(f), type(g)}
    if len(functypes) == 1:
        return functypes.pop()
    elif Function in functypes:
        return Function
    elif SymmetricFunction in functypes:
        return (functypes - {SymmetricFunction}).pop()
    return Function


class Function(bases.frozendict):
    """An immutable mapping between sets."""

    @classmethod
    def _new(cls, *args, **kwargs):
        # Bypass all verification and directly call Function constructor
        return super(Function, cls).__new__(cls, *args, **kwargs)

    def __new__(cls, *args, **kwargs):
        return cls._new(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        _ = self.image  # Ensure elements of the image are hashable

    def __iter__(self):
        """Return elements of the domain and their labels in pairs"""
        return iter(self.items())

    @cached_property
    def domain(self):
        """The set of objects for which f[x] is defined"""
        return frozenset(self.keys())

    @cached_property
    def image(self):
        """f.image <==> {f[x] for x in f.domain}"""
        return frozenset(self.values())

    def preimage(self):
        """f.preimage[y] <==> {x for x in f.domain if f[x] == y}"""
        preim = defaultdict(set)
        for x, y in self:
            preim[y].add(x)
        return bases.frozendict((y, frozenset(preim[y])) for y in self.image)

    def __mul__(self, other):
        """(f * g)[x] <==> f[g[x]]"""
        # f * g becomes a function on g's domain, so it inherits class of g
        return _result_functype(self, other)((x, self[y]) for x, y in other)


class Bijection(Function):
    """An invertible Function."""

    def __init__(self, *args, **kwargs):
        super(Bijection, self).__init__(*args, **kwargs)
        # Check cardinality of domain and codomain are identical
        if len(self) != len(self.image):
            raise ValueError("This function is not invertible.")

    @cached_property
    def inverse(self):
        """s.inverse <==> s**-1"""
        # Code taken directly from: "Inverting permutations in Python" at
        # http://stackoverflow.com/a/9185908.
        return self.__class__((y, x) for x, y in self)

    def conj(self, f):
        """s.conj(f) <==> s * f * s.inverse"""
        # Order of conjugation matters. Take the trees:
        #   1   2          a   b
        #    \ /    <==>    \ /
        #     3              c
        # whose nodes may be mapped to each other by:
        #   s(1) = a
        #   s(2) = b
        #   s(3) = c.
        # If f(1) = f(2) = f(3) = 3, and g(a) = g(b) = g(c) = c, then f is
        # related to g:  g(x) = s(f(s^-1(x))). We view conjugation *of* f as a
        # way to get *to* g.
        return f.__class__((y, self[f[x]]) for x, y in self)


class Endofunction(Function):
    """A Function whose domain contains its codomain."""

    def __init__(self, *args, **kwargs):
        super(Endofunction, self).__init__(*args, **kwargs)
        if not self.domain.issuperset(self.image):
            raise ValueError("image must be a subset of the domain")

    def __pow__(self, n):
        """f**n <==> the nth iterate of f"""
        # Convert to string of binary digits, clip off 0b, then reverse.
        component_iterates = bin(n)[2::][::-1]
        f = self
        f_iter = self.__class__((x, x) for x in self.domain)
        # Iterate by self-composing, akin to exponentiation by squaring.
        for it in component_iterates:
            if it == '1':
                f_iter *= f
            f *= f
        return f_iter

    @cached_property
    def imagepath(self):
        """f.imagepath[n] <==> len((f**n).image)"""
        cardinalities = [len(self.image)]
        f = self
        card_prev = len(self)
        for it in range(1, len(self)-1):
            f *= self
            card = len(f.image)
            cardinalities.append(card)
            # Save some time; if we have reached the fixed set, return.
            if card == card_prev:
                cardinalities.extend([card]*(len(self)-2-it))
                break
            card_prev = card
        return tuple(cardinalities)

    def enumerate_cycles(self):
        """Generate f's cycle decomposition in O(len(f)) time"""
        tried = set()
        cyclic = set()
        remaining = set(self.domain)
        while remaining:
            x = remaining.pop()
            path = [x]
            while x not in tried:
                remaining.discard(x)
                tried.add(x)
                x = self[x]
                path.append(x)
            if x not in cyclic:
                cycle = path[path.index(x)+1:]
                if cycle:
                    yield cycle
                    cyclic.update(cycle)

    @cached_property
    def cycles(self):
        """Return the set of f's cycles"""
        return frozenset(map(tuple, self.enumerate_cycles()))

    @cached_property
    def limitset(self):
        """x in f.limitset <==> any(x in cycle for cycle in f.cycles)"""
        return frozenset(flatten(self.cycles))

    @cached_property
    def acyclic_ancestors(self):
        """f.attached_treenodes[y] <==> f.preimage[y] - f.limitset"""
        descendants = defaultdict(set)
        for y, inv_image in self.preimage().items():
            for x in inv_image:
                if x not in self.limitset:
                    descendants[y].add(x)
        return bases.frozendict((x, frozenset(descendants[x])) for x in
                                self.domain)


class SymmetricFunction(Endofunction, Bijection):
    """A Bijective Endofunction"""

    def __init__(self, *args, **kwargs):
        super(SymmetricFunction, self).__init__(*args, **kwargs)

    def __pow__(self, n):
        """Symmetric functions allow us to take inverses."""
        if n >= 0:
            return super(SymmetricFunction, self).__pow__(n)
        else:
            return super(SymmetricFunction, self.inverse).__pow__(-n)


# Convenience functions for defining Endofunctions from a sequence in range(n)


def rangefunc(seq):
    """Return an Endofunction defined on range(len(seq))"""
    return Endofunction(enumerate(seq))


def rangeperm(seq):
    """Return a symmetric function defined on range(len(seq))"""
    return SymmetricFunction(enumerate(seq))


# Convenience functions for return random Functions


def randfunc(n):
    """ Return a random endofunction on n elements. """
    return rangefunc(random.randrange(n) for _ in range(n))


def randperm(n):
    """Return a random permutation of range(n)."""
    r = list(range(n))  # Explicitly call list for python 3 compatibility.
    random.shuffle(r)
    return rangeperm(r)


def randconj(f):
    """Return a random conjugate of f."""
    return randperm(len(f)).conj(f)


# Function enumerators


def _parsed_domain(domain):
    """Change domain to a frozenset. If domain is int, set to range(domain)."""
    if isinstance(domain, int):
        if domain < 0:
            raise ValueError("Cannot define domain on %s elements" % domain)
        domain = range(domain)
    return frozenset(domain)


class Mappings(bases.Enumerable):
    """The set of Functions between a domain and a codomain"""

    def __init__(self, domain, codomain):
        self.domain = _parsed_domain(domain)
        self.codomain = _parsed_domain(codomain)

    def __iter__(self):
        domain, codomain = map(sorted, [self.domain, self.codomain])
        for f in itertools.product(codomain, repeat=len(domain)):
            yield Function(zip(domain, f))

    def __len__(self):
        return len(self.codomain) ** len(self.domain)


class Isomorphisms(bases.Enumerable):
    """The set of bijections between a domain and a codomain"""

    def __init__(self, domain, codomain):
        domain = _parsed_domain(domain)
        codomain = _parsed_domain(codomain)
        if len(domain) != len(codomain):
            raise ValueError("Sets of size %s and %s cannot be isomorphic" % (
                len(domain), len(codomain)))
        self.domain = domain
        self.codomain = codomain

    def __iter__(self):
        domain, codomain = map(sorted, [self.domain, self.codomain])
        for p in itertools.permutations(codomain):
            yield Bijection(zip(domain, p))

    def __len__(self):
        return factorial(len(self.domain))


class TransformationMonoid(bases.Enumerable):
    """Set of all Endofunctions on a domain."""

    def __init__(self, domain):
        self.domain = _parsed_domain(domain)

    def __iter__(self):
        domain = sorted(self.domain)
        for f in itertools.product(domain, repeat=len(domain)):
            yield Endofunction(zip(domain, f))

    def __len__(self):
        return len(self.domain) ** len(self.domain)


class SymmetricGroup(bases.Enumerable):
    """The set of automorphisms on a domain"""

    def __init__(self, domain):
        self.domain = _parsed_domain(domain)

    def __iter__(self):
        domain = sorted(self.domain)
        for p in itertools.permutations(domain):
            yield SymmetricFunction(zip(domain, p))

    def __len__(self):
        return factorial(len(self.domain))
