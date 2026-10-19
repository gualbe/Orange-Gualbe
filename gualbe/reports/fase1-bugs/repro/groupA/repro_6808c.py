import os, csv
from Orange.widgets.data.owcsvimport import load_csv, Options, ColumnType, RowSpec
here = os.path.dirname(os.path.abspath(__file__))
for fn in ("na_small_string.csv", "na_300.csv"):
    for ct in (ColumnType.Auto, ColumnType.Categorical, ColumnType.Text):
        opts = Options(encoding="utf-8", dialect=csv.excel(),
                       columntypes=[(range(0, 1), ColumnType.Auto), (range(1, 2), ct)],
                       rowspec=[(range(0, 1), RowSpec.Header)])
        df = load_csv(os.path.join(here, fn), opts)
        print(fn, ct.name, df.dtypes.iloc[1], list(df.iloc[:4, 1]))
