"""#7020: Select Columns settings get mixed up between instances with similar
column names (context matching with global contexts)."""
import unittest
from unittest.mock import patch
from orangewidget.settings import SettingsHandler
import numpy as np
from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owselectcolumns import OWSelectAttributes

NAMES = ["VAR_A1", "VAR_A2", "VAR_A3", "VAR_B1", "VAR_C1", "VAR_C2", "VAR_C3"]


def table(names):
    dom = Domain([ContinuousVariable(n) for n in names])
    return Table.from_numpy(dom, np.random.RandomState(0).rand(5, len(names)))


def configure(w, keep):
    """Move every variable not in `keep` from 'used' to 'available'."""
    w.available_attrs[:] = [v for v in w.used_attrs if v.name not in keep]
    w.used_attrs[:] = [v for v in w.used_attrs if v.name in keep]
    w.commit.now()


def selected(test, w):
    out = test.get_output(w.Outputs.data, widget=w)
    return [v.name for v in out.domain.attributes]


class T(WidgetTest):
    def test_7020(self):
        D = table(NAMES)
        w1 = self.create_widget(OWSelectAttributes)
        w2 = self.create_widget(OWSelectAttributes)
        self.send_signal(w1.Inputs.data, D, widget=w1)
        self.send_signal(w2.Inputs.data, D, widget=w2)
        configure(w1, {"VAR_A1", "VAR_A2", "VAR_A3", "VAR_B1"})
        configure(w2, {"VAR_B1", "VAR_C1", "VAR_C2", "VAR_C3"})
        print("w1:", selected(self, w1)); print("w2:", selected(self, w2))
        # In Orange all instances of a class share one settings handler and
        # its global_contexts; WidgetTest creates a subclass per widget, so
        # share the list explicitly. Then both instances push their contexts
        # into the global contexts (happens when widgets/workflow are closed).
        # write_defaults is patched so that nothing is written to disk.
        w2.settingsHandler.global_contexts = w1.settingsHandler.global_contexts
        with patch.object(SettingsHandler, "write_defaults", lambda self: None):
            w2.settingsHandler.update_defaults(w2)
            w1.settingsHandler.update_defaults(w1)
        h = w1.settingsHandler

        # 1) new column appended
        D_new = table(NAMES + ["VAR_D1"])
        self.send_signal(w1.Inputs.data, D_new, widget=w1)
        print("1) w1 after new column appended  :", selected(self, w1))
        self.send_signal(w1.Inputs.data, D, widget=w1)
        print("   w1 after original data back   :", selected(self, w1))

        # 2) one of w1's columns missing/renamed in new data
        args = h.encode_domain(table([n if n != "VAR_A3" else "VAR_A3_renamed" for n in NAMES]).domain)
        print("   scores on renamed data: local", [round(h.match(c, None, *args), 2) for c in w1.context_settings],
              "global", [round(h.match(c, None, *args), 2) for c in h.global_contexts])
        D_missing = table([n if n != "VAR_A3" else "VAR_A3_renamed" for n in NAMES])
        self.send_signal(w1.Inputs.data, D_missing, widget=w1)
        print("2) w1 after VAR_A3 renamed       :", selected(self, w1))
        self.send_signal(w1.Inputs.data, D, widget=w1)
        print("   w1 after original data back   :", selected(self, w1))

        # 3) a fresh instance (e.g. third Select Columns in the workflow) gets data
        w3 = self.create_widget(OWSelectAttributes)
        w3.settingsHandler.global_contexts = h.global_contexts
        self.send_signal(w3.Inputs.data, D_missing, widget=w3)
        print("3) fresh w3 on renamed data      :", selected(self, w3))


if __name__ == "__main__":
    unittest.main()
