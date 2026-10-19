import re, unittest
from AnyQt.QtWidgets import QApplication
from Orange.data import Table, Domain
from Orange.classification import NaiveBayesLearner, LogisticRegressionLearner
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.ownomogram import OWNomogram, ProbabilitiesDotItem

def prob(w):
    mk = [i for i in w.scene.items() if isinstance(i, ProbabilitiesDotItem)][0]
    return re.search(r"Total: ([^ <]*).*Probability: (\d+)", mk.get_tooltip_text()).groups()

class T(WidgetTest):
    def test_x(self):
        data = Table("heart_disease")
        # same data, only longer attribute names -> identical model, different layout
        dom = Domain([a.renamed(a.name + " " + "x" * 40) for a in data.domain.attributes], data.domain.class_var)
        data2 = data.transform(dom) if False else Table.from_numpy(dom, data.X, data.Y)
        for lbl, d in [("short names", data), ("long names", data2)]:
            for ln, L in [("NB", NaiveBayesLearner()), ("LR", LogisticRegressionLearner(max_iter=1000))]:
                w = self.create_widget(OWNomogram)
                self.send_signal(w.Inputs.classifier, L(d))
                print(QApplication.platformName(), lbl, ln, "viewport", w.view.viewport().width(), "->", prob(w))
unittest.main(argv=["x", "T.test_x"], exit=False)
