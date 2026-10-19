import unittest

import numpy as np

from Orange.data import ContinuousVariable
from Orange.preprocess.discretize import Discretizer


class TestDiscretizerEq(unittest.TestCase):
    # gh-7065: points stored as arrays made == raise "truth value of an
    # array is ambiguous" (e.g. Group By on discretized dates)
    def test_eq_with_array_points(self):
        var = ContinuousVariable("x")
        a = Discretizer(var, np.array([1., 2.]))
        self.assertEqual(a, Discretizer(var, np.array([1., 2.])))
        self.assertEqual(a, Discretizer(var, [1., 2.]))
        self.assertNotEqual(a, Discretizer(var, np.array([1., 3.])))
        self.assertNotEqual(a, Discretizer(var, np.array([1.])))
        self.assertEqual(hash(a), hash(Discretizer(var, [1., 2.])))


if __name__ == "__main__":
    unittest.main()
