import unittest

import numpy as np

from Orange.misc._skl_compat import (
    deprecated_params, logistic_regression_params, mds_params,
    elastic_net_cv_params
)


class OldLR:
    def __init__(self, penalty="l2", C=1.0, n_jobs=None):
        pass


class NewLR:
    def __init__(self, penalty="deprecated", C=1.0, l1_ratio=0.0,
                 n_jobs=None):
        pass


class OldMDS:
    def __init__(self, metric=True, dissimilarity="euclidean"):
        pass


class NewMDS:
    def __init__(self, metric_mds=True, metric="euclidean", init="warn",
                 dissimilarity="deprecated"):
        pass


class OldENCV:  # scikit-learn < 1.7
    def __init__(self, n_alphas=100, alphas=None):
        pass


class MidENCV:  # scikit-learn 1.7 and 1.8
    def __init__(self, n_alphas="deprecated", alphas="warn"):
        pass


class NewENCV:  # scikit-learn >= 1.9
    def __init__(self, alphas=100):
        pass


class TestSklCompat(unittest.TestCase):
    def test_deprecated_params(self):
        self.assertEqual(deprecated_params(OldLR), frozenset())
        self.assertEqual(deprecated_params(NewLR), {"penalty"})

    def test_logistic_regression_params(self):
        params = {"penalty": "l1", "C": 2, "n_jobs": 1}
        self.assertEqual(logistic_regression_params(OldLR, params), params)
        self.assertEqual(logistic_regression_params(NewLR, params),
                         {"C": 2, "l1_ratio": 1.0})
        self.assertEqual(
            logistic_regression_params(NewLR, {"penalty": "l2", "C": 2}),
            {"C": 2, "l1_ratio": 0.0})
        self.assertEqual(
            logistic_regression_params(NewLR, {"penalty": None, "C": 2}),
            {"C": np.inf})
        elastic = {"penalty": "elasticnet", "C": 2}
        self.assertEqual(logistic_regression_params(NewLR, elastic), elastic)

    def test_mds_params(self):
        params = {"metric": False, "dissimilarity": "precomputed"}
        self.assertEqual(mds_params(OldMDS, params), params)
        self.assertEqual(mds_params(NewMDS, params),
                         {"metric_mds": False, "metric": "precomputed",
                          "init": "random"})

    def test_elastic_net_cv_params(self):
        params = {"n_alphas": 100, "alphas": 100, "eps": 0.001}
        self.assertEqual(elastic_net_cv_params(OldENCV, params),
                         {"n_alphas": 100, "alphas": None, "eps": 0.001})
        self.assertEqual(elastic_net_cv_params(MidENCV, params),
                         {"alphas": 100, "eps": 0.001})
        self.assertEqual(elastic_net_cv_params(NewENCV, params), params)
        explicit = {"n_alphas": 100, "alphas": [0.1, 1], "eps": 0.001}
        self.assertEqual(elastic_net_cv_params(OldENCV, explicit), explicit)


if __name__ == "__main__":
    unittest.main()
