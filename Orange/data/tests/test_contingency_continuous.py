import unittest

import numpy as np
import scipy.sparse as sp

from Orange.data import (
    Table, Domain, ContinuousVariable, DiscreteVariable, _contingency
)
from Orange.data.table import _contingency_continuous


class TestContingencyContinuous(unittest.TestCase):
    @staticmethod
    def _assert_same(expected, actual):
        (ev, ec), ecol, erow, eunk = expected
        (av, ac), acol, arow, aunk = actual
        np.testing.assert_array_equal(av, ev)
        np.testing.assert_array_equal(ac, ec)
        np.testing.assert_array_equal(acol, ecol)
        np.testing.assert_array_equal(arow, erow)
        assert aunk == eunk

    def test_matches_cython(self):
        rng = np.random.default_rng(42)
        for n, n_classes, rounding, nan_p in (
                (0, 2, None, 0), (1, 2, None, 0), (50, 1, 0, 0.1),
                (1000, 3, 1, 0.05), (1000, 7, None, 0.2),
                (5000, 2, 2, 0), (200, 5, 0, 0.9), (3000, 12, None, 0.1),
                (3000, 12, 1, 0.1), (3000, 40, 1, 0.1)):
            col = rng.standard_normal(n)
            if rounding is not None:
                col = np.round(col, rounding)
            col[rng.random(n) < nan_p] = np.nan
            if n > 3:
                col[:3] = [np.inf, -np.inf, 0]
            classes = rng.integers(0, n_classes, n).astype(float)
            classes[rng.random(n) < nan_p] = np.nan
            self._assert_same(
                _contingency.contingency_floatarray(col, classes, n_classes),
                _contingency_continuous(col, classes, n_classes, None))

    def test_falls_back_for_weights_and_invalid_classes(self):
        col = np.array([1., 2, 2, np.nan])
        classes = np.array([0., 1, 1, 0])
        weights = np.array([1., 2, 3, 4])
        self._assert_same(
            _contingency.contingency_floatarray(col, classes, 2, weights),
            _contingency_continuous(col, classes, 2, weights))
        with self.assertRaises(IndexError):
            _contingency_continuous(col, np.array([0., 1, 5, 0]), 2, None)

    def test_sparse_weighted_columns(self):
        # Weights of each column must be taken from the full weight vector,
        # not from the weights already subset for a previous column
        X = np.array([[1, 0, 2], [0, 3, 0], [4, 0, 5], [6, 7, 0], [0, 8, 9]],
                     dtype=float)
        y = np.array([0, 1, 0, 1, 1], dtype=float)
        W = np.array([1, 2, 3, 4, 5], dtype=float)
        domain = Domain([ContinuousVariable(f"x{i}") for i in range(3)],
                        DiscreteVariable("y", values=("a", "b")))
        table = Table.from_numpy(domain, sp.csr_matrix(X), y, W=W)
        for i, ((values, counts), *_) in enumerate(
                table._compute_contingency()[:3]):
            nonzero = X[:, i] != 0
            np.testing.assert_array_equal(values, np.unique(X[nonzero, i]))
            for c in (0, 1):
                for j, value in enumerate(values):
                    mask = nonzero & (X[:, i] == value) & (y == c)
                    self.assertEqual(counts[c, j], W[mask].sum())


if __name__ == "__main__":
    unittest.main()
