"""#6748: Aggregate Columns returns all NaN on sparse data."""
import unittest
import numpy as np
from Orange.data import Table
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owaggregatecolumns import OWAggregateColumns


class T(WidgetTest):
    def test_6748(self):
        dense = Table("iris")[:5]
        sparse = dense.to_sparse()
        for name, data in [("dense", dense), ("sparse", sparse)]:
            for op in ("Sum", "Mean", "Max", "Count non-zero"):
                w = self.create_widget(OWAggregateColumns)
                self.send_signal(w.Inputs.data, data, widget=w)
                w.selection_method = w.SelectAll
                w.operation = op
                w.commit.now()
                out = self.get_output(w.Outputs.data, widget=w)
                print(f"{name:6} {op:15}", out.get_column("agg"), flush=True)


if __name__ == "__main__":
    unittest.main()
