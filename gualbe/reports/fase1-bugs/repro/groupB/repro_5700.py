"""#5700: Venn Diagram crashes on sparse data (np.hstack in merge_data)."""
import unittest, traceback
from Orange.data import Table, Domain
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.owvenndiagram import OWVennDiagram


class T(WidgetTest):
    def run_venn(self, a, b, rowwise, label):
        w = self.create_widget(OWVennDiagram)
        w.rowwise = rowwise
        try:
            self.send_signal(w.Inputs.data, a, 1, widget=w)
            self.send_signal(w.Inputs.data, b, 2, widget=w)
            w.commit.now()
            sel = self.get_output(w.Outputs.selected_data, widget=w)
            ann = self.get_output(w.Outputs.annotated_data, widget=w)
            print(label, "OK annotated:", None if ann is None else ann.X.shape,
                  flush=True)
        except Exception as e:
            print(label, "EXC:", type(e).__name__, e, flush=True)
            traceback.print_exc(limit=-3)

    def test_5700(self):
        iris = Table("iris")
        d1 = iris[:100]
        d2 = iris[50:].transform(Domain(iris.domain.attributes[:3], iris.domain.class_var))
        for name, f in [("dense", lambda t: t), ("sparse", lambda t: t.to_sparse())]:
            for rowwise in (True, False):
                self.run_venn(f(d1), f(d2), rowwise, f"{name} rowwise={rowwise}")


if __name__ == "__main__":
    unittest.main()
