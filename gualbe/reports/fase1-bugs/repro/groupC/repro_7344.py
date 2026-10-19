import unittest, numpy as np
from Orange.data import Table, Domain, ContinuousVariable, DiscreteVariable
from Orange.classification import TreeLearner
from Orange.regression import TreeLearner as RTreeLearner
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.owpythagorastree import OWPythagorasTree
from Orange.widgets.visualize.pythagorastreeviewer import SquareGraphicsItem

def visible_squares(w):
    return sum(1 for it in w.scene.items() if isinstance(it, SquareGraphicsItem) and it.isVisible())

rng = np.random.default_rng(0)
X = rng.normal(size=(300, 50)); y = (X[:, 0] + X[:, 1] * X[:, 2] > 0).astype(float)
syn = Table.from_numpy(Domain([ContinuousVariable(f"f{i}") for i in range(50)],
                              DiscreteVariable("cls", values=("a", "b"))), X, y)

class T(WidgetTest):
    def test_fresh(self):
        for name, data, lrn in [("iris", Table("iris"), TreeLearner()),
                                ("titanic", Table("titanic"), TreeLearner()),
                                ("housing", Table("housing"), RTreeLearner()),
                                ("synthetic50", syn, TreeLearner())]:
            w = self.create_widget(OWPythagorasTree)
            m = lrn(data)
            self.send_signal(w.Inputs.tree, m, widget=w)
            print(f"fresh {name}: nodes={m.node_count()} depth={m.depth()} depth_limit={w.depth_limit} visible squares={visible_squares(w)}")

    def test_context_depth(self):
        iris = Table("iris")
        w = self.create_widget(OWPythagorasTree)
        trivial = TreeLearner(max_depth=0)(iris) if True else None
        print("trivial depth:", trivial.depth(), "nodes:", trivial.node_count())
        self.send_signal(w.Inputs.tree, trivial, widget=w)
        print("after trivial tree: depth_limit=", w.depth_limit, "squares=", visible_squares(w))
        deep = TreeLearner()(iris)
        self.send_signal(w.Inputs.tree, deep, widget=w)
        print(f"after deep tree (same class var): depth={deep.depth()} nodes={deep.node_count()} depth_limit={w.depth_limit} slider max={w.depth_slider.maximum()} squares={visible_squares(w)}")
        # new widget instance: context stored in settings (simulate by reusing stored settings)
        st = self.widget_settings = w.settingsHandler.pack_data(w)
        w2 = self.create_widget(OWPythagorasTree, stored_settings=st)
        self.send_signal(w2.Inputs.tree, deep, widget=w2)
        print(f"new widget w/ saved settings: depth_limit={w2.depth_limit} squares={visible_squares(w2)}")
unittest.main()
