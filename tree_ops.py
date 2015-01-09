#!/usr/bin/env python
# Copyright (C) 2014 Caleb Levy - All Rights Reserved.
# 
# The terms of use, license and copyright information for the code and ideas 
# contained herein are described in the LICENSE file included with this 
# project. For more information please contact me at caleb.levy@berkeley.edu.

import numpy as np
import unittest

def Unpack(PList): # Extract the next level of a rooted tree
    PList = [M for M in PList if isinstance(M,list)]
    UP = []    
    for M in PList:
        for El in M:
            UP.append(El)            
    return UP
    
def ListNestedEls(Tree,d): # List all elements at depth d, representing nodes with further connections as their own trees
    for I in range(d):
        Tree = Unpack(Tree)
    return Tree
        
def Unwind(Tree): # Give all the elements in the nodes of a tree
    S = []
    while Tree:
        M = [I for I in Tree if not isinstance(I,list)]
        for El in M:
            S.append(El)
        Tree = Unpack(Tree)
    return list(set(S))
        
def numels_by_nestdepth(Tree): # Find the level path of a rooted tree, including 1 in the base
    L = []
    L.append(1)
    while Tree:
        L.append(len(Tree))
        Tree = Unpack(Tree)
    return L
    
def GetTreeEl(Tree,Ind):
    if len(Ind) == 1:
        return Tree[Ind[0]]
    else:
        return GetTreeEl(Tree[Ind[0]],Ind[1:])
    
def ChangeTreeEl(Tree,Ind,El):
    if not hasattr(Tree,'__iter__'):
        raise ValueError('Tree depth exceeded')
    if not hasattr(Ind,'__iter__'):
        Tree[Ind] = El
    elif len(Ind) == 1:
        Tree[Ind[0]] = El
    else:
        ChangeTreeEl(Tree[Ind[0]],Ind[1:],El)
        
def IImage(f): # Return the inverse image of S under f
    N = len(f)
    S = range(N)
    Im = [None]*N
    for I in range(N):
        Im[I] = [J for J in S if f[J]==I]               
    return Im
    
def TreeForm(f):
    N = len(f)
    S = range(N)
    Im = IImage(f)
    Fix = [I for I in S if f[I]==I]
    
    assert len(Fix) == 1 # The tree better be rooted, or we will have an infinite loop
    
    Fix = Fix[0]
    Tree = Im[Fix]
    Tree.remove(Fix)
    
    IndSet = [[I] for I in range(len(Tree))]
    
    while IndSet:
        NewSet = []
        for Ind in IndSet:
            El = GetTreeEl(Tree,Ind)
            range(len(Im[El]))
            for I in range(len(Im[El])):
                IndN = Ind[:]
                IndN.append(I)
                NewSet.append(IndN)
            
            ChangeTreeEl(Tree,Ind,Im[El])
                
        IndSet = NewSet
        
    return Tree

class NestedtreeTest(unittest.TestCase):
    funcforms = [
        [0, 0, 1, 2, 3, 4, 2, 0, 7, 8],
        [0, 0, 1, 2, 3, 4, 2, 0, 7, 7],
        [0, 0, 1, 2, 3, 3, 3, 3, 3, 0],
    ]
    nestedforms = [
        [[[[[[]]], []]], [[[]]]],
        [[[[[[]]], []]], [[], []]],
        [[[[[], [], [], [], []]]], []]
    ]
    
    def testTreeform(self):
        for I, tree in enumerate(self.funcforms):
            self.assertEqual(self.nestedforms[I], TreeForm(tree))
    

if __name__ == '__main__':
    unittest.main()