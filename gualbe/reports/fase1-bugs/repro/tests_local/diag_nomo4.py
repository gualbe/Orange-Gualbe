import re, unittest
from AnyQt.QtWidgets import QApplication
from Orange.data import Table, Domain
from Orange.classification import NaiveBayesLearner
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.ownomogram import OWNomogram, ProbabilitiesDotItem
def prob(w):
    mk = [i for i in w.scene.items() if isinstance(i, ProbabilitiesDotItem)][0]
    return re.search(r"Total: ([^ <]*).*Probability: (\d+)", mk.get_tooltip_text()).groups()
class T(WidgetTest):
    def test_x(self):
        data = Table("heart_disease")
        cls = NaiveBayesLearner()(data)
        for width in (400, 500, 600, 800, 1200):
            w = self.create_widget(OWNomogram)
            w.show(); w.resize(width, 700); QApplication.processEvents()
            self.send_signal(w.Inputs.classifier, cls); QApplication.processEvents()
            print(QApplication.platformName(), "window", width, "viewport", w.view.viewport().width(), "->", prob(w))
            w.hide()
unittest.main(argv=["x", "T.test_x"], exit=False)
