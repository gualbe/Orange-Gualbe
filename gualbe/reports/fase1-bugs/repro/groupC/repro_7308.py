import unittest, numpy as np
from Orange.data import Table, Domain, DiscreteVariable, ContinuousVariable
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.owscatterplot import OWScatterPlot

def data(values):
    domain = Domain([DiscreteVariable("category", values=values), ContinuousVariable("value")])
    return Table.from_numpy(domain, np.array([[0, 0], [1, 0.5]]))

class T(WidgetTest):
    def test_axis(self):
        w = self.create_widget(OWScatterPlot)
        d1 = data(("1", "2"))
        self.send_signal(w.Inputs.data, d1, widget=w)
        w.attr_x, w.attr_y = d1.domain["category"], d1.domain["value"]
        w.attr_changed()
        w.controls.graph.attr_color if False else None
        w.graph.controls.attr_color if False else None
        w.attr_color = d1.domain["category"]; w.graph.update_colors()
        ax = w.graph.plot_widget.plotItem.getAxis("bottom")
        legend = lambda: [it[1].text for it in w.graph.color_legend.items]
        print("before: x ticks", ax._tickLevels, "| legend", legend())
        d2 = data(("a", "b"))
        self.send_signal(w.Inputs.data, d2, widget=w)
        print("after : x ticks", ax._tickLevels, "| legend", legend())
        print("attr_x values:", w.attr_x.values, "| domain checksum equal:", d1.domain.checksum() == d2.domain.checksum())
unittest.main(defaultTest="T.test_axis")
