#!/usr/bin/env python
# Copyright (C) 2015 Caleb Levy - All Rights Reserved.
#
# The terms of use, license and copyright information for the code and ideas
# contained herein are described in the LICENSE file included with this
# project. For more information please contact me at caleb.levy@berkeley.edu.

import unittest

from endofunction_structures.productrange import *


class ProductrangeTest(unittest.TestCase):

    def test_productrange(self):
        """Test number of outputs in the product range is correct."""
        begins = [[1], None,   0,      1,      [1]*4,   [3]*4,  (1, 2, 3, 3)]
        ends = [[0],   [4]*4,  [4]*4,  [7]*3,  [10]*4,  [6]*4,  (2, 4, 8, 10)]
        steps = [None, 1,      None,   2,      3,       None,   (1, 1, 2, 2)]
        counts = [0,   4**4,   4**4,   3**3,   3**4,    3**4,   1*2*3*4]

        begins.extend([(1, 2, 3), (1, 2, 3)])
        ends.extend([(-9, 9, 9),  (9, -9, 9)])
        steps.extend([(-3, 3, 3), (3, -3, 3)])
        counts.extend([4*3*2,     4*3*2])
        for c, b, e, s in zip(counts, begins, ends, steps):
            self.assertEqual(c, len(list(productrange(b, e, s))))
            self.assertEqual(c, len(list(rev_range(b, e, s))))
