import unittest, numpy as np
from Orange.data import Table, Domain, ContinuousVariable, DiscreteVariable
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.owscatterplot import OWScatterPlot

class T(WidgetTest):
    def test_size(self):
        rng = np.random.default_rng(0)
        n = 2000
        d = Table.from_numpy(Domain([ContinuousVariable("x"), ContinuousVariable("y")], DiscreteVariable("c", values=("a","b","c"))),
                             rng.normal(size=(n, 2)), rng.integers(0, 3, n).astype(float))
        w = self.create_widget(OWScatterPlot)
        w.resize(1000, 700); w.show()
        self.send_signal(w.Inputs.data, d, widget=w)
        w.report_html = ""
        w.send_report()
        sz = len(w.report_html)
        print(f"one scatter report item ({n} pts, offscreen dpr=1): {sz/1e6:.2f} MB of HTML; "
              f"plots fitting in 2 MB setHtml limit ~ {2e6/sz:.1f}")
unittest.main(defaultTest="T.test_size")
