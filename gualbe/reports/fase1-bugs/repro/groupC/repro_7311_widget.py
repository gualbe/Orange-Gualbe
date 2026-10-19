import unittest, numpy as np
from Orange.data import Table, Domain
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.model.owknn import OWKNNLearner

class T(WidgetTest):
    def test_stale_V(self):
        w = self.create_widget(OWKNNLearner)
        w.metric_index = 3  # mahalanobis
        w.settings_changed() if hasattr(w, "settings_changed") else None
        iris = Table("iris")
        self.send_signal(w.Inputs.data, iris, widget=w)
        self.assertIsNotNone(self.get_output(w.Outputs.model, widget=w))
        d = iris.domain
        iris3 = iris.transform(Domain(d.attributes[:3], d.class_var))
        self.send_signal(w.Inputs.data, iris3, widget=w)
        print("model after 2nd input:", self.get_output(w.Outputs.model, widget=w))
        print("errors:", [str(m) for m in w.Error.active])
        # fresh widget on iris3 works
        w2 = self.create_widget(OWKNNLearner); w2.metric_index = 3; w2.settings_changed()
        self.send_signal(w2.Inputs.data, iris3, widget=w2)
        print("fresh widget model:", self.get_output(w2.Outputs.model, widget=w2) is not None, [str(m) for m in w2.Error.active])
unittest.main(defaultTest="T.test_stale_V")
