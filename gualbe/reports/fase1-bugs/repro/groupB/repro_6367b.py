"""#6367 (extra): Select Columns with AttributeList containing a hidden var."""
import unittest
from Orange.data import Table
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owselectcolumns import OWSelectAttributes
from Orange.widgets.widget import AttributeList


class T(WidgetTest):
    def test_sel(self):
        iris = Table("iris")
        dom = iris.domain.copy()
        dom.attributes[0].attributes["hidden"] = True
        data = iris.transform(dom)
        w = self.create_widget(OWSelectAttributes)
        self.send_signal(w.Inputs.data, data, widget=w)
        print("used attrs model:", [v.name for v in w.used_attrs], flush=True)
        print("available:", [v.name for v in w.available_attrs], flush=True)
        w.use_input_features = True
        self.send_signal(w.Inputs.features, AttributeList(data.domain[:2]), widget=w)
        out = self.get_output(w.Outputs.data, widget=w)
        print("out attrs:", [v.name for v in out.domain.attributes], flush=True)


if __name__ == "__main__":
    unittest.main()
