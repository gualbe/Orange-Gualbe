import re, sys
import numpy as np
from Orange.data import Table
from Orange.classification import NaiveBayesLearner, LogisticRegressionLearner
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.tests.utils import simulate
from Orange.widgets.visualize.ownomogram import OWNomogram, ProbabilitiesDotItem
import unittest

def prob(w):
    m = [i for i in w.scene.items() if isinstance(i, ProbabilitiesDotItem)][0]
    t = m.get_tooltip_text()
    return re.search(r"Total: ([^ <]*).*Probability: (\d+)", t).groups()

class T(WidgetTest):
    def test(self):
        data = Table("heart_disease")
        for name, cls in [("nb", NaiveBayesLearner()(data)), ("lr", LogisticRegressionLearner(max_iter=1000)(data))]:
            w = self.create_widget(OWNomogram)
            self.send_signal(w.Inputs.classifier, cls)
            print(name, "view size", w.view.size(), "scene rect", w.scene.sceneRect())
            for i in range(w.class_combo.count()):
                simulate.combobox_activate_index(w.class_combo, i)
                print(name, "class", i, "initial", prob(w))
                w.controls.scale.buttons[0].click(); print("  point scale", prob(w))
                w.n_spin.setValue(5); print("  n=5", prob(w))
                simulate.combobox_activate_index(w.cont_feature_dim_combo, 1); print("  2D", prob(w))
                w.controls.scale.buttons[1].click(); w.n_spin.setValue(10)
                simulate.combobox_activate_index(w.cont_feature_dim_combo, 0); print("  reset", prob(w))
            # expected prob of "mean"/default instance
unittest.main(argv=["x"], exit=False)
