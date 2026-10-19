import re, unittest
import numpy as np
from AnyQt.QtWidgets import QApplication
from Orange.data import Table
from Orange.classification import LogisticRegressionLearner, NaiveBayesLearner
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.tests.utils import simulate
from Orange.widgets.visualize.ownomogram import OWNomogram, ProbabilitiesDotItem
def prob(w):
    mk = [i for i in w.scene.items() if isinstance(i, ProbabilitiesDotItem)][0]
    return int(re.search(r"Probability: (\d+)", mk.get_tooltip_text()).group(1))
class T(WidgetTest):
    def test_x(self):
        iris = Table("iris")
        inst = iris[53:54]
        for name, L in [("LR", LogisticRegressionLearner()), ("NB", NaiveBayesLearner())]:
            model = L(iris)
            p_model = model(inst, model.Probs)[0]
            for norm in (True, False):
                w = self.create_widget(OWNomogram)
                w.show(); w.resize(900, 700); QApplication.processEvents()
                w.normalize_probabilities = norm
                self.send_signal(w.Inputs.classifier, model)
                self.send_signal(w.Inputs.data, inst)
                got = []
                for i in range(w.class_combo.count()):
                    simulate.combobox_activate_index(w.class_combo, i)
                    got.append(prob(w))
                print(name, "normalize=%s" % norm, "model %:", np.round(100 * p_model).astype(int).tolist(), "nomogram %:", got)
                w.hide()
unittest.main(argv=["x", "T.test_x"], exit=False)
