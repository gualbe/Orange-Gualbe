from unittest.mock import patch

import numpy as np
from orangewidget.settings import SettingsHandler

from Orange.data import Table, Domain, ContinuousVariable
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owselectcolumns import OWSelectAttributes

NAMES = ["VAR_A1", "VAR_A2", "VAR_A3", "VAR_B1", "VAR_C1", "VAR_C2", "VAR_C3"]


def _table(names):
    domain = Domain([ContinuousVariable(n) for n in names])
    return Table.from_numpy(domain, np.random.RandomState(0).rand(5, len(names)))


class TestOwnContextPreferred(WidgetTest):
    # gh-7020: with a variable missing, a widget took the selection of
    # another Select Columns, whose (global) context scored higher
    def _configure(self, widget, keep):
        widget.available_attrs[:] = \
            [v for v in widget.used_attrs if v.name not in keep]
        widget.used_attrs[:] = [v for v in widget.used_attrs if v.name in keep]
        widget.commit.now()

    def _selected(self, widget):
        out = self.get_output(widget.Outputs.data, widget=widget)
        return [v.name for v in out.domain.attributes]

    def test_keeps_own_selection_when_a_column_is_missing(self):
        data = _table(NAMES)
        w1 = self.create_widget(OWSelectAttributes)
        w2 = self.create_widget(OWSelectAttributes)
        self.send_signal(w1.Inputs.data, data, widget=w1)
        self.send_signal(w2.Inputs.data, data, widget=w2)
        self._configure(w1, {"VAR_A1", "VAR_A2", "VAR_A3", "VAR_B1"})
        self._configure(w2, {"VAR_B1", "VAR_C1", "VAR_C2", "VAR_C3"})
        # in Orange, all instances share global contexts
        w2.settingsHandler.global_contexts = \
            w1.settingsHandler.global_contexts
        with patch.object(SettingsHandler, "write_defaults", lambda _: None):
            w2.settingsHandler.update_defaults(w2)
            w1.settingsHandler.update_defaults(w1)

        renamed = _table([n if n != "VAR_A3" else "VAR_A3_x" for n in NAMES])
        self.send_signal(w1.Inputs.data, renamed, widget=w1)
        selected = self._selected(w1)
        self.assertIn("VAR_A1", selected)
        self.assertNotIn("VAR_C1", selected)
