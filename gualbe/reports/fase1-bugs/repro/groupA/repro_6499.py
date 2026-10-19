import os, csv, warnings
import pandas as pd
from Orange.data import Table
from Orange.widgets.data.owcsvimport import load_csv, Options, ColumnType, RowSpec, guess_data_type
here = os.path.dirname(os.path.abspath(__file__))
for name, rows in {"first_ambiguous": ["08/03/18", "28/03/18", "01/12/19"],
                   "first_unambiguous": ["28/03/18", "08/03/18", "01/12/19"]}.items():
    fn = os.path.join(here, f"dates_{name}.csv")
    with open(fn, "w") as f:
        f.write("d,x\n" + "".join(f"{d},{i}\n" for i, d in enumerate(rows)))
    print("====", name, rows)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        print("  pandas guess_data_type :", list(guess_data_type(pd.Series(rows, dtype=object)).astype(str)),
              "| warnings:", [str(x.message)[:60] for x in w])
    opts = Options(encoding="utf-8", dialect=csv.excel(),
                   columntypes=[(range(0, 1), ColumnType.Auto), (range(1, 2), ColumnType.Auto)],
                   rowspec=[(range(0, 1), RowSpec.Header)])
    df = load_csv(fn, opts); print("  CSV Import Auto   :", list(df.iloc[:, 0].astype(str)))
    opts = opts._replace(columntypes=[(range(0, 1), ColumnType.Time), (range(1, 2), ColumnType.Auto)]) if hasattr(opts, "_replace") else Options(encoding="utf-8", dialect=csv.excel(), columntypes=[(range(0, 1), ColumnType.Time), (range(1, 2), ColumnType.Auto)], rowspec=[(range(0, 1), RowSpec.Header)])
    df = load_csv(fn, opts); print("  CSV Import Time   :", list(df.iloc[:, 0].astype(str)))
    t = Table.from_file(fn); v = t.domain["d"]
    print("  File (core reader):", type(v).__name__, [v.str_val(x) for x in t.get_column("d")])
