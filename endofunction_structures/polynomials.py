#!/usr/bin/env python
# Copyright (C) 2014-2015 Caleb Levy - All Rights Reserved.
#
# The terms of use, license and copyright information for the code and ideas
# contained herein are described in the LICENSE file included with this
# project. For more information please contact me at caleb.levy@berkeley.edu.

""" Enumerate and produce polynomials of various kinds. """


from functools import reduce
import numpy as np

from . import multiset
from . import productrange


def monomial_symmetric_polynomial(x, powers):
    """ Symmetric monomial polynomial with partition of powers [p_1, ..., p_j]
    evaluated at the vector of values [x_1, ..., x_n]. The partition is further
    split into two vectors:

        (e_1, e_2, ..., e_l) - vector of exponent values;
        (m_1, m_2, ..., m_l) - vector of multiplicities of each exponent

    Instead of summing over all possible monomial terms, we use the recursion
    relation

        T(n, m_1, ..., m_l) =   T(n-1, m_1, ..., m_l)
                              + x_n**e_1 * T(n-1, m_1-1, m_2, ..., m_l)
                              + x_n**e_2 * T(n-1, m_1, m_2-1, ..., m_l)
                              + ...
                              + x_n**e_l * T(n-1, m_1, m_2, ..., m_l-1),

    where T(n, m_1, ..., m_l) is the symmetric monomial polynomial with the
    same powers evaluated with multiplicities (m_1, ..., m_l). This exploits
    additive and multiplicative associativity and commutativity to avoid
    repeated work.

    This algorithm runs in O(n * m_1 *...* m_k) steps, and requires an array of
    size O(m_1 *...* m_j) for storing previous terms of the recurrence. For
    fun, you can input an array of symbolic variables from sympy and get fast
    evaluation of many variable polynomials via a numpy array with object
    elements. """

    n = len(x)
    pows, mults = multiset.Multiset(powers).split()
    l = len(pows)
    shape = tuple(i+2 for i in mults)

    # Contains 1, possibly 2 more dimensions than necessary.
    T = np.ndarray(shape, object)
    T[:] = 0
    T[(1, )*l] = 1

    # The powers use up sum(multiplcities) of the original x.
    for k in range(n-sum(mults)+1):
        for ind in productrange.productrange(1, shape):
            fac = x[k+sum(ind)-l-1]
            for j in range(l):
                ind_prev = list(ind)
                ind_prev[j] -= 1
                T[ind] += fac**pows[j]*T[tuple(ind_prev)]

    return T[tuple(i-1 for i in shape)]


def poly_multiply(coeffs1, coeffs2):
    """
    Given numerical lists c and d of length n and m, returns the coefficients
    of P(X)*Q(X) in decreasing order, where
        P(X) = c[-1] + c[-2]*X + ... + c[0]*x^n
        Q(X) = d[-1] + d[-2]*X + ... + d[0]*x^m

    For some reason sympy and numpy do not seem to have this capacity easily
    accessible, or at least nothing dedicated to the purpose. Very likely to be
    faster than the expand method.

    Source taken from:
        "How can I multiply two polynomials in Python using a loop and by
        calling another function?" at http://stackoverflow.com/a/18116401.
    """
    final_coeffs = [0] * (len(coeffs1)+len(coeffs2)-1)
    for ind1, coef1 in enumerate(coeffs1):
        for ind2, coef2 in enumerate(coeffs2):
            final_coeffs[ind1 + ind2] += coef1 * coef2
    return final_coeffs


def FOIL(roots):
    """First Outer Inner Last

    Given a list of values roots, return the polynomial of degree len(roots)+1
    with leading coefficient 1 given by
        (X - roots[0]) * (X - roots[1]) * ... * (X - roots[-1])
    """
    monomials = [(1, -root) for root in roots]
    return reduce(poly_multiply, monomials, [1])
