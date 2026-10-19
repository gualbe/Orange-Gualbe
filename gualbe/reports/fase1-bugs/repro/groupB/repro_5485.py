"""#5485: Color widget - (a) pickling of settings with Feature Constructor vars,
(b) stale data after input changes (same names/values, different compute_value),
(c) IndexError in DiscColorTableModel.setData when editing an 'empty' cell
    (row with fewer values than the widest row; reached by tabbing)."""
import io, pickle, unittest, traceback
from unittest.mock import patch
from orangewidget.settings import SettingsHandler
import numpy as np
from AnyQt.QtCore import Qt
from AnyQt.QtTest import QTest
from AnyQt.QtWidgets import QApplication
from Orange.data import Table, Domain, DiscreteVariable, ContinuousVariable
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owcolor import OWColor, ColorRole
from Orange.widgets.data.owfeatureconstructor import (
    construct_variables, DiscreteDescriptor, ContinuousDescriptor)


def constructed(data, expr):
    vars_ = construct_variables(
        [DiscreteDescriptor("big", "'yes' if petal_length > 4 else 'no'", (), False),
         ContinuousDescriptor("c", expr, 2)], data)
    dom = Domain(data.domain.attributes + tuple(vars_), data.domain.class_vars)
    return data.transform(dom)


class T(WidgetTest):
    def test_a_pickle(self):
        data = constructed(Table("iris"), "sepal_length * 2")
        w = self.create_widget(OWColor)
        self.send_signal(w.Inputs.data, data, widget=w)
        w.disc_model.setData(w.disc_model.index(0, 1), (255, 0, 0), ColorRole)
        w.disc_model.setData(w.disc_model.index(0, 0), "renamed", Qt.EditRole)
        try:
            # write_defaults patched: pickle into memory only, nothing on disk
            with patch.object(SettingsHandler, 'write_defaults', lambda self: None):
                w.settingsHandler.update_defaults(w)
            buf = io.BytesIO()
            w.settingsHandler.write_defaults_file(buf)
            print("(a) pickling defaults OK,", len(buf.getvalue()), "bytes", flush=True)
            pickle.dumps(w.settingsHandler.pack_data(w))
            print("(a) pickling pack_data OK", flush=True)
        except Exception as e:
            print("(a) EXC:", type(e).__name__, e, flush=True)

    def test_b_stale(self):
        iris = Table("iris")
        d1 = constructed(iris, "sepal_length * 2")
        d2 = constructed(iris, "sepal_length * 100")
        w = self.create_widget(OWColor)
        self.send_signal(w.Inputs.data, d1, widget=w)
        w.cont_model.setData(w.cont_model.index(4, 0), "C!", Qt.EditRole)
        w.disc_model.setData(w.disc_model.index(0, 1), (255, 0, 0), ColorRole)
        out1 = self.get_output(w.Outputs.data, widget=w)
        self.send_signal(w.Inputs.data, d2, widget=w)
        out2 = self.get_output(w.Outputs.data, widget=w)
        print("(b) out1 C! :", out1.get_column("C!")[:3],
              " out2 C! :", out2.get_column("C!")[:3],
              " expected out2:", d2.get_column("c")[:3], flush=True)

    def test_c_index_error(self):
        data = Table("heart_disease")  # discrete vars with different #values
        w = self.create_widget(OWColor)
        self.send_signal(w.Inputs.data, data, widget=w)
        m = w.disc_model
        nvals = [len(d.var.values) for d in m.attrdescs]
        print("(c) values per row:", nvals, "columnCount:", m.columnCount(), flush=True)
        row = nvals.index(min(nvals))
        col = nvals[row] + 1  # first 'empty' cell of that row
        print("(c) flags of empty cell editable?",
              bool(m.flags(m.index(row, col)) & Qt.ItemIsEditable), flush=True)
        try:
            m.setData(m.index(row, col), "x", Qt.EditRole)
            print("(c) setData OK", flush=True)
        except Exception as e:
            print("(c) EXC:", type(e).__name__, e, flush=True)
            traceback.print_exc(limit=-2)
        # simulate user: edit name of a variable, then press Tab repeatedly
        view = w.disc_view
        w.show()
        errors = []
        orig = m.setData
        def wrapped(*a):
            try:
                return orig(*a)
            except Exception as e:
                errors.append(e)
                return False
        m.setData = wrapped
        view.setCurrentIndex(m.index(row, 0))
        view.edit(m.index(row, 0))
        for _ in range(nvals[row] + 3):
            QApplication.processEvents()
            ed = QApplication.focusWidget()
            QTest.keyClick(ed if ed is not None else view, Qt.Key_Tab)
        QApplication.processEvents()
        print("(c) after tabbing: current col", view.currentIndex().column(),
              "errors:", [repr(e) for e in errors], flush=True)


if __name__ == "__main__":
    unittest.main()
