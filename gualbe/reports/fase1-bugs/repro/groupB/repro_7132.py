"""#7132: Merge Data, PCA(iris) + iris, row index, Concatenate tables -> crash."""
import sys, unittest, traceback
from Orange.data import Table
from Orange.projection import PCA
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owmergedata import OWMergeData, INDEX


def run(w, data, extra):
    w.send_signal(w.Inputs.data, data) if False else None


class T(WidgetTest):
    def _merge(self, data, extra):
        w = self.create_widget(OWMergeData)
        self.send_signal(w.Inputs.data, data, widget=w)
        self.send_signal(w.Inputs.extra_data, extra, widget=w)
        print("pairs:", w.attr_boxes.current_state(), flush=True)
        w.attr_boxes.set_state([(INDEX, INDEX)])
        w.merging = w.OuterJoin   # "Concatenate tables"
        try:
            out = w.merge()
            print("OK output", None if out is None else out.X.shape, flush=True)
            return out
        except Exception as e:
            print("EXC:", type(e).__name__, e, flush=True)
            traceback.print_exc(limit=-4)

    def test_7132(self):
        iris = Table("iris")
        proj = PCA(n_components=2)(iris)
        print("-- full overlap (issue scenario)")
        self._merge(proj(iris), iris)
        print("-- partial overlap (data=first 100 rows of PCA)")
        out = self._merge(proj(iris[:100]), iris)
        if out is not None:
            print(out[[98, 99, 100, 101]])


if __name__ == "__main__":
    unittest.main()
