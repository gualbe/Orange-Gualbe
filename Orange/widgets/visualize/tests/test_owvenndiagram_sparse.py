import numpy as np

from Orange.data import Table, Domain
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.owvenndiagram import OWVennDiagram


class TestVennSparse(WidgetTest):
    # gh-5700: columns of sparse tables are sparse matrices, which could not
    # be stacked with np.hstack
    def test_sparse_data(self):
        iris = Table("iris")
        d1 = iris[:100]
        d2 = iris[50:].transform(
            Domain(iris.domain.attributes[:3], iris.domain.class_var))
        for rowwise in (True, False):
            dense = self._run(d1, d2, rowwise)
            sparse = self._run(d1.to_sparse(), d2.to_sparse(), rowwise)
            if dense is None:
                self.assertIsNone(sparse)
            else:
                np.testing.assert_equal(
                    sparse.X.toarray() if hasattr(sparse.X, "toarray")
                    else sparse.X, dense.X)

    def _run(self, d1, d2, rowwise):
        w = self.create_widget(OWVennDiagram)
        w.rowwise = rowwise
        self.send_signal(w.Inputs.data, d1, 1, widget=w)
        self.send_signal(w.Inputs.data, d2, 2, widget=w)
        w.commit.now()
        return self.get_output(w.Outputs.annotated_data, widget=w)
