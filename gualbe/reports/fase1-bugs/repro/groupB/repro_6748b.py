"""#6748 (collateral): Table.add_column into X of a sparse table is lost ->
Concatenate with source column as attribute on sparse data gives NaN."""
import unittest
from Orange.data import Table
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owconcatenate import OWConcatenate


class T(WidgetTest):
    def test_concat(self):
        for name, d in [("dense", Table("iris")[:3]), ("sparse", Table("iris")[:3].to_sparse())]:
            w = self.create_widget(OWConcatenate)
            self.send_signal(w.Inputs.additional_data, d, 0, widget=w)
            self.send_signal(w.Inputs.additional_data, d, 1, widget=w)
            w.append_source_column = True
            w.source_column_role = w.AttributeRole
            w.commit.now()
            out = self.get_output(w.Outputs.data, widget=w)
            print(name, "Source ID column:", out.get_column("Source ID"), flush=True)


if __name__ == "__main__":
    unittest.main()
