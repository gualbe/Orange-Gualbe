import numpy as np

from Orange.data import Table
from Orange.projection import PCA
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owmergedata import OWMergeData, INDEX


class TestMergeWithoutUnmatchedRows(WidgetTest):
    def test_outer_join_with_shared_compute_values(self):
        # gh-7132: with no unmatched rows on the right, an empty table was
        # transformed and PCA's shared compute value failed on it
        iris = Table("iris")
        projected = PCA(n_components=2)(iris)(iris)
        w = self.create_widget(OWMergeData)
        self.send_signal(w.Inputs.data, projected, widget=w)
        self.send_signal(w.Inputs.extra_data, iris, widget=w)
        w.attr_boxes.set_state([(INDEX, INDEX)])
        w.merging = w.OuterJoin
        out = w.merge()
        self.assertEqual(out.X.shape, (150, 6))
        np.testing.assert_almost_equal(out.X[:, 2:], iris.X)
