"""#6721: DomainContextHandler ignores variable position (attrs/metas).
Test case from the issue, plus the exclude_attributes workaround."""
import unittest, traceback
from Orange.data import Table, Domain
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.widget import OWWidget
from Orange.widgets.gui import comboBox
from Orange.widgets.settings import ContextSetting, DomainContextHandler
from Orange.widgets.utils.itemmodels import DomainModel
from orangewidget.utils.signals import Input


def make_widget(exclude):
    class OWProblem(OWWidget):
        name = "Context Problem"
        v1 = ContextSetting(None)
        v2 = ContextSetting(None, exclude_attributes=exclude)
        settingsHandler = DomainContextHandler()

        class Inputs:
            data = Input("Data", Table, default=True)

        def __init__(self):
            super().__init__()
            m1 = DomainModel(DomainModel.SEPARATED, valid_types=DomainModel.PRIMITIVE)
            comboBox(self.controlArea, self, "v1", model=m1, label="All")
            m2 = DomainModel(DomainModel.METAS | DomainModel.CLASSES,
                             valid_types=DomainModel.PRIMITIVE)
            comboBox(self.controlArea, self, "v2", model=m2, label="Metas + Classes")
            self.contextAboutToBeOpened.connect(lambda x: self.init_interface(x[0]))

        def init_interface(self, data):
            domain = data.domain if data is not None else None
            self.controls.v1.model().set_domain(domain)
            self.controls.v2.model().set_domain(domain)

        @Inputs.data
        def set_data(self, data):
            self.closeContext()
            self.openContext(data)
    return OWProblem


class T(WidgetTest):
    def check(self, exclude):
        w = self.create_widget(make_widget(exclude))
        iris = Table("iris")
        petals_in_metas = Domain(iris.domain.attributes[:2], iris.domain.class_var,
                                 metas=iris.domain.attributes[2:])
        self.send_signal(w.Inputs.data, iris.transform(petals_in_metas), widget=w)
        w.v1 = iris.domain["sepal width"]
        w.v2 = iris.domain["petal width"]
        try:
            self.send_signal(w.Inputs.data, iris, widget=w)
            print(f"exclude_attributes={exclude}: OK v1={w.v1} v2={w.v2}", flush=True)
        except Exception as e:
            print(f"exclude_attributes={exclude}: EXC {type(e).__name__}: {e}", flush=True)
        # can the widget be used with iris afterwards? (send again)
        try:
            self.send_signal(w.Inputs.data, iris, widget=w)
            print("   resend iris OK", flush=True)
        except Exception as e:
            print("   resend iris EXC:", e, flush=True)

    def test_6721(self):
        self.check(False)
        self.check(True)


if __name__ == "__main__":
    unittest.main()
