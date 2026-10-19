import unittest

import numpy as np
import scipy.stats

from Orange.statistics.util import nanmode


def _scipy_nanmode(x, axis):
    all_nan = np.isnan(x).sum(axis=axis, keepdims=True) == x.shape[axis]
    res = scipy.stats.mode(x, axis, keepdims=True)
    return (np.where(all_nan, np.nan, res.mode),
            np.where(all_nan, np.nan, res.count))


class TestFastNanmode(unittest.TestCase):
    def test_matches_scipy(self):
        rng = np.random.default_rng(0)
        pools = [np.array([0, 1, 2, 3.]), np.array([-1, 0, 2.5, np.inf]),
                 np.array([7.0, 1e9]), None]
        for trial in range(400):
            pool = pools[trial % len(pools)]
            shape = (rng.integers(1, 30), rng.integers(1, 4))
            x = rng.choice(pool, shape) if pool is not None \
                else np.round(rng.standard_normal(shape), 1)
            x[rng.random(shape) < rng.random()] = np.nan
            for axis in (0, 1):
                mode, count = nanmode(x, axis)
                exp_mode, exp_count = _scipy_nanmode(x, axis)
                np.testing.assert_equal(mode, exp_mode)
                np.testing.assert_equal(count, exp_count)
            mode, count = nanmode(x[:, 0], 0)
            exp_mode, exp_count = _scipy_nanmode(x[:, 0], 0)
            np.testing.assert_equal(mode, exp_mode)
            np.testing.assert_equal(count, exp_count)

    def test_nan_wins_only_if_more_frequent(self):
        nan = np.nan
        self.assertEqual(nanmode(np.array([1, 1, nan, nan]), 0)[0][0], 1)
        self.assertTrue(np.isnan(nanmode(np.array([1, nan, nan]), 0)[0][0]))


if __name__ == "__main__":
    unittest.main()
