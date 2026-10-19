"""#7065: Discretize (datetime with missing values) -> Group By crashes in openContext."""
import unittest, traceback
import numpy as np
from Orange.data import Table, Domain, TimeVariable, ContinuousVariable
from Orange.preprocess import Discretize
from Orange.preprocess.discretize import EqualWidth, FixedTimeWidth, EqualFreq
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owgroupby import OWGroupBy


def make(nan=True):
    t = TimeVariable("date", have_date=True)
    x = ContinuousVariable("x")
    ts = np.array([t.parse(s) for s in
                   ["2024-01-05", "2024-02-10", "2024-03-15", "2024-04-20",
                    "2024-05-25", "2024-06-30"]], dtype=float)
    if nan:
        ts[2] = np.nan
    X = np.c_[ts, np.arange(6.)]
    return Table.from_numpy(Domain([t, x]), X)


class T(WidgetTest):
    def run_gb(self, data, label):
        w = self.create_widget(OWGroupBy)
        try:
            self.send_signal(w.Inputs.data, data, widget=w)
            out = self.get_output(w.Outputs.data, widget=w)
            print(label, "OK; gb_attrs:", w.gb_attrs, "out:",
                  None if out is None else len(out), flush=True)
        except Exception as e:
            print(label, "EXC:", type(e).__name__, e, flush=True)
            traceback.print_exc(limit=-3)
        return w

    def test_7065(self):
        for nan in (False, True):
            data = make(nan)
            for name, method in [("EqualWidth", EqualWidth(n=3)),
                                 ("FixedTimeWidth(1 month)", FixedTimeWidth(1, 1)),
                                 ("EqualFreq", EqualFreq(n=3))]:
                try:
                    d = Discretize(method=method)(data)
                except Exception as e:
                    print(nan, name, "discretize EXC", e); continue
                dv = d.domain[0]
                print(f"nan={nan} {name}: values={dv.values}", flush=True)
                # same widget receives the data twice (reopen context)
                self.run_gb(d, f"  nan={nan} {name} [fresh]")
                w = self.create_widget(OWGroupBy)
                self.send_signal(w.Inputs.data, d, widget=w)
                try:
                    self.send_signal(w.Inputs.data, d, widget=w)
                    print("  resend OK", flush=True)
                except Exception as e:
                    print("  resend EXC:", type(e).__name__, e, flush=True)
                    traceback.print_exc(limit=-3)
                # equality of variable
                r = dv == Discretize(method=method)(data).domain[0]
                print("  type(var == var2):", type(r), flush=True)


if __name__ == "__main__":
    unittest.main()
