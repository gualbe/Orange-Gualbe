import os, csv
from Orange.data import Table
from Orange.widgets.data.owcsvimport import load_csv, Options, ColumnType, RowSpec, pandas_to_table
here = os.path.dirname(os.path.abspath(__file__))
fn = os.path.join(here, "bigdec.csv")
with open(fn, "w") as f:
    f.write("a;b\n-22112248,96;1,5\n123,45;2,5\n-1,5;3,5\n")
class D(csv.excel): delimiter = ";"
opts = Options(encoding="utf-8", dialect=D(), columntypes=[(range(0, 2), ColumnType.Auto)],
               rowspec=[(range(0, 1), RowSpec.Header)], decimal_separator=",", group_separator="")
df = load_csv(fn, opts)
print("pandas dtypes:", list(df.dtypes), "values:", df.iloc[:, 0].tolist())
t = pandas_to_table(df)
v = t.domain["a"]
print("var:", repr(v), "number_of_decimals:", v.number_of_decimals, "format_str:", v._format_str if hasattr(v, "_format_str") else None)
print("stored X:", t.X[:, 0].tolist())
print("str_val:", [v.str_val(x) for x in t.X[:, 0]])
print("repr(t[0]):", t[0])
# Compare: File widget (core reader) with same file -> probably treated as text
t2 = Table.from_file(fn); print("File reader domain:", t2.domain, [type(x).__name__ for x in t2.domain.variables + t2.domain.metas])
# writer output
from Orange.data.io import CSVReader
out = os.path.join(here, "bigdec_out.csv"); CSVReader.write_file(out, t); print("written:", open(out).read().splitlines())
# Effect of number_of_decimals on a var read with '.' decimal
fn3 = os.path.join(here, "bigdec_dot.csv"); open(fn3, "w").write("a\n-22112248.96\n1.5\n")
t3 = Table.from_file(fn3); v3 = t3.domain["a"]; print("dot file: decimals", v3.number_of_decimals, [v3.str_val(x) for x in t3.X[:, 0]])
