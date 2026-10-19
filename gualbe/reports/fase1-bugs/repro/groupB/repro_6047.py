"""#6047: DBSCAN - saved eps (neighbourhood distance) is overwritten whenever
data arrives (workflow load or upstream change)."""
import unittest
from Orange.data import Table
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.unsupervised.owdbscan import OWDBSCAN


class T(WidgetTest):
    def test_6047(self):
        iris = Table("iris")
        # 1) workflow load: stored setting eps=0.09 (inside k-distance range? see below)
        w = self.create_widget(OWDBSCAN, stored_settings={"eps": 0.09})
        print("eps before data:", w.eps, flush=True)
        self.send_signal(w.Inputs.data, iris, widget=w)
        print("k-distance range: [%.3f, %.3f]" % (w.k_distances.min(), w.k_distances.max()))
        print("1) stored eps=0.09 -> after data:", round(w.eps, 4), flush=True)
        # 2) in-range value saved in workflow
        w = self.create_widget(OWDBSCAN, stored_settings={"eps": 0.3})
        self.send_signal(w.Inputs.data, iris, widget=w)
        print("2) stored eps=0.3  -> after data:", round(w.eps, 4), flush=True)
        # 3) user sets eps manually, then upstream re-sends (e.g. a parameter changed)
        w.controls.eps.setValue(0.25)
        print("3) user set eps:", w.eps, end="; ", flush=True)
        self.send_signal(w.Inputs.data, iris[::-1], widget=w)
        print("after upstream re-send:", round(w.eps, 4), flush=True)
        out = self.get_output(w.Outputs.annotated_data, widget=w)
        print("   clusters in output use eps", round(w.model.projector.eps, 4)
              if hasattr(w, "model") else "?")


if __name__ == "__main__":
    unittest.main()
