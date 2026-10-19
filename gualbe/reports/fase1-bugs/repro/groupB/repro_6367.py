"""#6367: widgets with hidden variables (var.attributes['hidden']=True)."""
import unittest, traceback
from Orange.data import Table, Domain
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.utils.annotated_data import ANNOTATED_DATA_SIGNAL_NAME
from Orange.widgets.visualize.owscatterplot import OWScatterPlot
from Orange.widgets.visualize.owsieve import OWSieveDiagram
from Orange.widgets.data.owgroupby import OWGroupBy
from Orange.widgets.data.owaggregatecolumns import OWAggregateColumns
from Orange.widgets.data.owselectcolumns import OWSelectAttributes
from Orange.widgets.utils.state_summary import format_summary_details
from Orange.data.util import get_unique_names
from Orange.widgets.data.utils.preprocess import *  # noqa
from orangewidget.utils.signals import summarize
from Orange.widgets.widget import AttributeList


def hidden_iris(idx=0):
    iris = Table("iris")
    dom = iris.domain.copy()
    dom.attributes[idx].attributes["hidden"] = True
    return iris.transform(dom)


def step(label, f):
    try:
        r = f()
        print(label, "OK", "" if r is None else r, flush=True)
    except Exception as e:
        print(label, "EXC:", type(e).__name__, e, flush=True)
        traceback.print_exc(limit=-3)


class T(WidgetTest):
    def test_scatter(self):
        data = hidden_iris(0)
        hv = data.domain[0]
        w = self.create_widget(OWScatterPlot)
        self.send_signal(w.Inputs.data, data, widget=w)
        vr = w.vizrank_dialog
        print("scatter xy_model contains hidden?", hv in list(w.xy_model), flush=True)
        states = list(vr.state_generator())
        attrs = vr.attrs
        print("scatter vizrank attrs:", [a.name for a in attrs], flush=True)
        # try every pair as if selected in vizrank
        def sel_all():
            for i, a in enumerate(attrs):
                for b in attrs[i + 1:]:
                    w.set_attr((a, b))
        step("scatter set_attr for all vizrank pairs", sel_all)
        # explicitly set a pair with hidden var (as old vizrank would)
        step("scatter set_attr((hidden, other))",
             lambda: w.set_attr((hv, data.domain[1])))
        # features input with hidden var
        step("scatter features=[hidden, x]", lambda: (self.send_signal(
            w.Inputs.features, AttributeList(data.domain[:2]), widget=w),
            (w.attr_x, w.attr_y))[1])

    def test_groupby(self):
        data = hidden_iris(0)
        w = self.create_widget(OWGroupBy)
        step("groupby hidden data", lambda: self.send_signal(w.Inputs.data, data, widget=w))
        # context saved with visible var, then data where it's hidden
        w2 = self.create_widget(OWGroupBy)
        iris = Table("iris")
        self.send_signal(w2.Inputs.data, iris, widget=w2)
        w2.gb_attrs = [iris.domain[0]]
        step("groupby context with now-hidden var",
             lambda: (self.send_signal(w2.Inputs.data, data, widget=w2),
                      [v.name for v in w2.gb_attrs])[1])
        out = self.get_output(w2.Outputs.data, widget=w2)
        print("   groupby output:", None if out is None else len(out), flush=True)

    def test_sieve(self):
        data = hidden_iris(0)
        w = self.create_widget(OWSieveDiagram)
        self.send_signal(w.Inputs.data, data, widget=w)
        print("sieve attr model contains hidden?",
              data.domain[0] in list(w.controls.attr_x.model()), flush=True)
        step("sieve features=[hidden, x]", lambda: (self.send_signal(
            w.Inputs.features, AttributeList(data.domain[:2]), widget=w),
            (w.attr_x, w.attr_y, w.canvas.items().__len__()))[1])

    def test_aggregate(self):
        data = hidden_iris(0)
        w = self.create_widget(OWAggregateColumns)
        self.send_signal(w.Inputs.data, data, widget=w)
        step("aggregate features=[hidden, x]", lambda: (self.send_signal(
            w.Inputs.features, AttributeList(data.domain[:2]), widget=w),
            self.get_output(w.Outputs.data, widget=w).get_column("agg")[:3])[1])

    def test_selectcols(self):
        data = hidden_iris(0)
        w = self.create_widget(OWSelectAttributes)
        self.send_signal(w.Inputs.data, data, widget=w)
        step("selectcols features=[hidden]", lambda: (self.send_signal(
            w.Inputs.features, AttributeList(data.domain[:1]), widget=w),
            self.get_output(w.Outputs.data, widget=w).domain)[1])


if __name__ == "__main__":
    unittest.main()
