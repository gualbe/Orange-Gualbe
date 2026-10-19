import os, numpy as np
from Orange.data import Table
here = os.path.dirname(os.path.abspath(__file__))
fn = os.path.join(here, "na_small_string.csv")
with open(fn, "w") as f:
    f.write("id,PD\n0,NA\n1,PD\n2,XY\n3,AB\n4,CD\n")
t = Table.from_file(fn)
v = t.domain["PD"]; print("core reader small:", type(v).__name__, list(t.get_column("PD")))
# File widget: change type text<->categorical
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owfile import OWFile
from Orange.widgets.data.owcsvimport import OWCSVFileImport, load_csv, Options, ColumnType
from Orange.widgets.utils.domaineditor import Column
WidgetTest.setUpClass()
wt = WidgetTest(); wt.setUp() if hasattr(wt, "setUp") else None
for n in (5, 300):
    fn2 = fn if n == 5 else os.path.join(here, "na_300.csv")
    w = wt.create_widget(OWFile)
    w.add_path(fn2); w.load_data()
    out = wt.get_output(w.Outputs.data, widget=w)
    print(f"\nOWFile n={n}: as read:", type(out.domain['PD']).__name__,
          [str(x) for x in out[:6, 'PD'].get_column('PD')] if out.domain['PD'].is_string else [out.domain['PD'].str_val(x) for x in out.get_column('PD')[:6]])
    model = w.domain_editor.model()
    row = [r[Column.name] for r in model.variables].index("PD")
    for newtype in ("categorical", "text"):
        model.setData(model.index(row, Column.tpe), newtype)
        w.apply_domain_edit()
        out = wt.get_output(w.Outputs.data, widget=w)
        var = out.domain['PD']
        col = out.get_column('PD')
        shown = [var.str_val(x) for x in col[:6]]
        print(f"  -> set to {newtype}: {type(var).__name__}, first values {shown}")
