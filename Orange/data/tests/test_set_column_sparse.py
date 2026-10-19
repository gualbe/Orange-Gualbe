import unittest

import numpy as np
import scipy.sparse as sp

from Orange.data import Table, ContinuousVariable, Domain


class TestSetColumnSparse(unittest.TestCase):
    # gh-6748: on sparse X, a column is a copy, so values were lost
    def test_add_column_to_sparse_x(self):
        iris = Table("iris").to_sparse()
        var = ContinuousVariable("new")
        table = iris.add_column(var, np.arange(len(iris), dtype=float))
        self.assertTrue(sp.issparse(table.X))
        np.testing.assert_equal(table.get_column(var), np.arange(len(iris)))
        np.testing.assert_equal(table.X[:, :4].toarray(), iris.X.toarray())

    def test_set_column_scalar(self):
        table = Table("iris").to_sparse()
        with table.unlocked():
            table.set_column(1, 7)
        np.testing.assert_equal(table.get_column(1), 7)

    def test_set_column_in_sparse_metas(self):
        iris = Table("iris")
        domain = Domain(iris.domain.attributes, iris.domain.class_var,
                        [ContinuousVariable("m")])
        table = Table.from_numpy(domain, iris.X, iris.Y,
                                 sp.csr_matrix(np.ones((len(iris), 1))))
        with table.unlocked():
            table.set_column("m", np.arange(len(iris), dtype=float))
        self.assertTrue(sp.issparse(table.metas))
        np.testing.assert_equal(table.get_column("m"), np.arange(len(iris)))


if __name__ == "__main__":
    unittest.main()
