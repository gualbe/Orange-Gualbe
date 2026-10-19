"""#5914: Edit Domain - re-merging with a larger N ("all except N most frequent")
has no effect: values previously merged into 'other' stay merged."""
import unittest
from unittest.mock import patch
from AnyQt.QtCore import Qt
from AnyQt.QtWidgets import QDialog
from Orange.widgets.tests.base import GuiTest
from Orange.widgets.data.oweditdomain import (
    DiscreteVariableEditor, GroupItemsDialog, Categorical)

N = None


def fake_exec(self):
    self.n_values_radio.setChecked(True)
    self.n_values_spin.setValue(N)
    return QDialog.Accepted


class T(GuiTest):
    @patch.object(GroupItemsDialog, "exec", fake_exec)
    def test_5914(self):
        global N
        w = DiscreteVariableEditor()
        cats = tuple("abcdef")
        v = Categorical("C", cats, ())
        # frequencies a:6 b:5 c:4 d:3 e:2 f:1
        values = [i for i, n in enumerate([6, 5, 4, 3, 2, 1]) for _ in range(n)]
        w.set_data_categorical(v, values)
        model = w.values_edit.model()
        show = lambda: [model.index(i, 0).data(Qt.EditRole) for i in range(model.rowCount())]
        for n in (2, 4, 1):
            N = n
            w.values_edit.selectionModel().clear()
            w.merge_items.trigger()
            print(f"after merge keeping {n} most frequent:", show(), flush=True)
        print("transform:", w.get_data()[1], flush=True)


if __name__ == "__main__":
    unittest.main()
