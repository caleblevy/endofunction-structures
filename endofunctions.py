"""endofunctions.py
Let S be a finite set with N elements; i.e. |S|=N. There are N^N endofunctions defined on this set, and we shall denote
the set of all such objects by S^S.

For a given f in S^S, its image will have n=|f(S)| elements for n in range(1,N+1). Similarly it's second iterate will
have |f(f(S))|=m<=n elements. Once |f^(k)(S)|=|f^(k+1)(S)| then |f^(j)(S)|=|f^(k)(S)| for k>j. The list of sizes of
images of iterates of f from 1 to n-1 is called the "image path" of f.

This file mainly exists to calculate the distribution of image sizes of the iterates of all endofunctions on a set S.
The naive way to do this is to literally enumerate every endofunction. This works for n up to about 8 on a decent
desktop computer.

The second, far more efficient method, is to enumerate the endofunction structures on S (i.e. orbits of the
transformation monoid under the action of conjugation by the symmetric group), and then add up the multiplicities of
each structure. This runs in roughly O(4^n) time. This is still quite horrendous, but it enables us to get up to n=16
before being intolerably slow.

Various special cases can be done much faster. This distribution of (first iterate) image sizes can be done in O(n^2)
and the final set can be O(n).
"""

from iteration import product_range, compositions
from endofunction_structures import endofunction_structures, structure_multiplicity, endofunction_to_func
import numpy as np
import unittest
from math import factorial
from necklaces import nCk

endofunctions = lambda n: product_range([n]*n)

def imagepath(f):
    """
    Given a list f of length n such that all([I in range(n) for I in f]), 
    """
    n = len(f)
    cardinalities = [len(set(f))]
    f_orig = f[:]
    card_prev = n
    for it in range(1,n-1):
        f = [f_orig[x] for x in f]
        card = len(set(f))
        cardinalities.append(len(set(f)))
        if card == card_prev:
            cardinalities.extend([card]*(n-2-it))
            break
        card_prev = card
    return cardinalities

def iterate_imagedist_brute(n):
    """
    The most naive, straightforward way to calculate the distribution of 
    """
    M = np.zeros((n,n-1), dtype=object)
    for f in endofunctions(n):
        im = imagepath(f)
        for it, card in enumerate(im):
            M[card-1,it] += 1
    return M

def iterate_imagedist_endofunction(n):
    if n == 1:
        return np.array([1],dtype=object)
        
    M = np.zeros((n,n-1), dtype=object)
    for func_struct in endofunction_structures(n):
        mult = structure_multiplicity(func_struct)
        f = endofunction_to_func(func_struct)
        im = imagepath(f)
        for it, card in enumerate(im):
            M[card-1,it] += mult
    return M

iterate_imagedist = iterate_imagedist_endofunction

def firstdist_composition(n):
    """
    Count OEIS A090657 using integer compositions in O(2^n) time
    """
    if n == 1:
        return [1]
        
    F = [0]*n
    for comp in product_range([2]*(n-1)):
        val = n
        rep = 1
        for I in comp:
            if not I:
                val *= rep
            else:
                val *= n - rep
                rep += 1
        F[rep-1] += val
    return F

def firstdists_upto(N):
    """
    Count OEIS A090657 using recursion relation in O(n^2) time. This is the fastest method I know of and probably the
    fastest there is.
    
    # TODO - Figure out the logic that went into this and the previous one and latex it up.
    """
    FD = np.zeros((N,N), dtype=object)
    for n in xrange(N):
        FD[0,n] = FD[n,n] = 1
        for I in xrange(n):
            FD[I,n] = FD[I-1,n-1] + (I+1)*FD[I,n-1]
    
    for n in xrange(N):
        for I in xrange(n+1):
            FD[I,n] *= factorial(n+1)/factorial(n-I)

    return FD
    
firstdist_recurse = firstdist = lambda n: list(firstdists_upto(n)[:,-1])

'''
Top row: OEIS A236396 - labelled rooted trees of height at most k on n nodes
Right column: OEIS A066324, A219694 (reverse), A243203
'''

def nCk_grid(N):
    """nCk(n,k) == nCk_table[n,k] for 0 <= k <= n <= N"""
    binomial_coeffs = np.zeros((N+1, N+1), dtype=object)
    for I in xrange(N+1):
        for J in xrange(N+1):
            binomial_coeffs[I,J] = nCk(I,J)
    return binomial_coeffs

def powergrid(N):
    """I**J == power_grid[I,J] for 0 <= I, J <= N. Note 0^0 defined as 1."""
    base = np.arange(N+1, dtype=object)
    [bases, exponents] = np.meshgrid(base, base)
    exponentials = bases**exponents
    return exponentials.T

def lastdist_comp(N):
    L = [0]*N
    exponentials = powergrid(N)
    binomial_coeffs = nCk_grid(N)
    for n in range(N-1,0,-1):
        L[n] = factorial(N)/factorial(N-n)
        
        V = [0]*(N-n+1)
        V[0] = n
        V[1] = N-n
        
        tot = 0
        go = True
        
    

class EndofunctionTest(unittest.TestCase):
    iterate_imagedists = [
        np.array([[3, 9],
                  [18, 12],
                  [6, 6]],
                  dtype=object),
                  
        np.array([[4, 40, 64,],
                  [84, 120, 96],
                  [144, 72, 72],
                  [24, 24, 24]],
                  dtype=object),
                  
        np.array([[5, 205, 505, 625],
                  [300, 1060, 1120, 1000],
                  [1500, 1260, 900, 900],
                  [1200, 480, 480, 480],
                  [120, 120, 120, 120]], 
                  dtype=object)
              ]
    
    firstdists = [
        [2,2],
        [3,18,6],
        [4,84,144,24],
        [5,300,1500,1200,120],
        [6,930,10800,23400,10800,720],
        [7,2646,63210,294000,352800,105840,5040]
        ]
        
    def testImagepath(self):
        """Check various special and degenerate cases, with right index"""
        self.assertEqual([1], imagepath([0]))
        self.assertEqual([1], imagepath([0,0]))
        self.assertEqual([1], imagepath([1,1]))
        self.assertEqual([2], imagepath([0,1]))
        self.assertEqual([2], imagepath([1,0]))
        node_count = [2,3,5,15]
        for n in node_count:
            tower = [0] + range(n-1)
            cycle = [n-1] + range(n-1)
            fixed = range(n)
            degen = [0]*n
            self.assertEqual(range(n)[:0:-1], imagepath(tower))
            self.assertEqual([n]*(n-1), imagepath(cycle))
            self.assertEqual([n]*(n-1), imagepath(fixed))
            self.assertEqual([1]*(n-1), imagepath(degen))
    
    def testIterateImagedist(self):
        """Check the star of the show; an exponential time algorithm for finding the multiplicities of image"""
        for dist in self.iterate_imagedists:
            n = dist.shape[0]
            np.testing.assert_array_equal(dist, iterate_imagedist_brute(n))
            np.testing.assert_array_equal(dist, iterate_imagedist_endofunction(n))
    
    def testFirstdist(self):
        """Left column: OEIS A101817 (A090657). Test number of endofunctions on n elements whose image has size k."""
        for dist in self.firstdists:
            n = len(dist)
            self.assertEqual(dist, firstdist_composition(n))
            self.assertEqual(dist, list(iterate_imagedist(n)[:,0]))
            self.assertEqual(dist, firstdist_recurse(n))
        
if __name__ == '__main__':
    unittest.main()
        
        
