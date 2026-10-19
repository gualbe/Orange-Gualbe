import os, csv
import numpy as np
from Orange.data import Table
from Orange.data.io_util import guess_data_type
from Orange.widgets.data.owcsvimport import load_csv, Options, ColumnType, RowSpec
here = os.path.dirname(os.path.abspath(__file__))
ids = ["10213407285517229", "10155206846088649", "2049903568368818", "10211717072377002", "123"]
for ext, sep in ((".csv", ","), (".tab", "\t")):
    fn = os.path.join(here, "bigids" + ext)
    with open(fn, "w") as f:
        f.write(sep.join(["id", "x"]) + "\n" + "".join(f"{i}{sep}{k}\n" for k, i in enumerate(ids)))
    t = Table.from_file(fn); v = t.domain["id"]
    col = t.get_column("id")
    print(ext, type(v).__name__, "values as float->int:", [int(x) for x in col] if v.is_continuous else list(col))
    print("   str_val:", [v.str_val(x) for x in col])
    lost = [a for a, x in zip(ids, col) if v.is_continuous and str(int(x)) != a]
    print("   precision lost for:", lost)
vm, vals, ct = guess_data_type(np.array(ids, dtype=object))
print("guess_data_type ->", ct.__name__)
# Write back out
from Orange.data.io import CSVReader
t = Table.from_file(os.path.join(here, "bigids.csv"))
out = os.path.join(here, "bigids_roundtrip.csv"); CSVReader.write_file(out, t)
print("roundtrip:", open(out).read().splitlines()[:3])
opts = Options(encoding="utf-8", dialect=csv.excel(),
               columntypes=[(range(0, 2), ColumnType.Auto)], rowspec=[(range(0, 1), RowSpec.Header)])
df = load_csv(os.path.join(here, "bigids.csv"), opts)
print("CSV Import dtype:", df.dtypes.iloc[0], list(df.iloc[:2, 0]))
from Orange.widgets.data.owcsvimport import pandas_to_table
tt = pandas_to_table(df); vv = tt.domain["id"]; print("CSV Import table:", type(vv).__name__, [vv.str_val(x) for x in tt.get_column("id")[:2]], [int(x) for x in tt.get_column("id")[:2]])
