import unittest

import numpy as np

from Orange.base import Learner, Model
from Orange.data import Table


class _KeepAll(Learner):
    preprocessors = []

    def fit_storage(self, data):
        return Model(data.domain)


class TestUsedValsUnknownClass(unittest.TestCase):
    def test_unknown_class_values_are_ignored(self):
        # nan cast to int gave a garbage class index in used_vals
        iris = Table("iris")
        with iris.unlocked(iris.Y):
            iris.Y[:5] = np.nan
        model = _KeepAll()(iris)
        self.assertEqual(len(model.used_vals), 1)
        np.testing.assert_equal(model.used_vals[0], [0, 1, 2])


if __name__ == "__main__":
    unittest.main()
