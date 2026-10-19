import unittest

import numpy as np

from Orange.data import Table
from Orange.classification import KNNLearner
from Orange.regression import KNNRegressionLearner


class TestKNNMahalanobis(unittest.TestCase):
    def test_learner_is_not_modified_by_fit(self):
        # gh-7311: the covariance of the first fit was stored in the learner
        # and reused for later fits (e.g. in all folds of cross validation)
        iris = Table("iris")
        learner = KNNLearner(metric="mahalanobis")
        learner(iris[:75])
        self.assertIsNone(learner.params["metric_params"])
        refit = learner(iris[75:])
        fresh = KNNLearner(metric="mahalanobis")(iris[75:])
        np.testing.assert_equal(refit(iris), fresh(iris))

    def test_predict_with_brute_force(self):
        # scikit-learn's brute-force algorithm requires VI, not V
        for name in ("zoo", "heart_disease"):
            data = Table(name)
            model = KNNLearner(metric="mahalanobis", algorithm="brute")(data)
            self.assertEqual(len(model(data[:5])), 5)

    def test_regression(self):
        housing = Table("housing")
        model = KNNRegressionLearner(metric="mahalanobis")(housing)
        self.assertEqual(len(model(housing[:5])), 5)

    def test_single_feature(self):
        iris = Table("iris")[:, [0, 4]]
        model = KNNLearner(metric="mahalanobis")(iris)
        self.assertEqual(len(model(iris[:5])), 5)


if __name__ == "__main__":
    unittest.main()
