import re
from AnyQt.QtWidgets import QApplication, QGraphicsTextItem
from AnyQt.QtGui import QFontMetrics, QFontInfo
from Orange.data import Table
from Orange.classification import NaiveBayesLearner
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.ownomogram import OWNomogram, ProbabilitiesDotItem
import Orange.widgets.visualize.ownomogram as m
import unittest
orig = OWNomogram.create_main_nomogram
def patched(self, attributes, attr_inds, name_items, points, max_width, point_text, name_offset):
    print("viewport w=", self.view.viewport().rect().width(), "name_offset=", round(name_offset,1), "max_width=", round(max_width,1))
    return orig(self, attributes, attr_inds, name_items, points, max_width, point_text, name_offset)
OWNomogram.create_main_nomogram = patched
class T(WidgetTest):
    def test_x(self):
        t = QGraphicsTextItem("Probabilities (%)")
        f = t.font(); print("platform", QApplication.platformName(), "font", QFontInfo(f).family(), QFontInfo(f).pointSizeF(), "text w", t.boundingRect().width())
        w = self.create_widget(OWNomogram)
        self.send_signal(w.Inputs.classifier, NaiveBayesLearner()(Table("heart_disease")))
        mk = [i for i in w.scene.items() if isinstance(i, ProbabilitiesDotItem)][0]
        print(re.search(r"Total.*%", mk.get_tooltip_text()).group(0))
unittest.main(argv=["x", "T.test_x"], exit=False)
