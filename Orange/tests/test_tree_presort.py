import unittest

import numpy as np

from Orange.data import Table
from Orange.classification import TreeLearner


def _structure(node):
    if node is None:
        return [None]
    threshold = getattr(node, "threshold", None)
    out = [(type(node).__name__, getattr(node, "attr_idx", None),
            None if threshold is None else float(threshold),
            tuple(node.subset))]
    for child in node.children or []:
        out += _structure(child)
    return out


class TestTreePresort(unittest.TestCase):
    """Sorting attributes once at the root must give the same tree as
    sorting them at each node"""

    def _assert_same_tree(self, data, **kwargs):
        learner = TreeLearner(**kwargs)
        active = np.nonzero(~np.isnan(data.Y))[0].astype(np.int32)
        presorted = learner._build_tree(
            data, active, sorted_idx=learner._presort(data[active]))
        sorted_at_nodes = learner._build_tree(data, active)
        self.assertEqual(_structure(presorted), _structure(sorted_at_nodes))

    def test_same_tree(self):
        rng = np.random.default_rng(0)
        iris = Table("iris")
        ties = iris.copy()
        with ties.unlocked(ties.X):
            ties.X[:] = np.round(ties.X)
            ties.X[rng.random(ties.X.shape) < 0.1] = np.nan
        for data in (iris, ties, Table("heart_disease"), Table("zoo")):
            for kwargs in ({}, {"binarize": True},
                           {"min_samples_leaf": 5, "max_depth": 4}):
                self._assert_same_tree(data, **kwargs)

    def test_sparse_is_not_presorted(self):
        self.assertIsNone(TreeLearner._presort(Table("iris").to_sparse()))


if __name__ == "__main__":
    unittest.main()
