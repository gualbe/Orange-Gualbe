import os, numpy as np
from Orange.data import Table
here = os.path.dirname(os.path.abspath(__file__))
def write(fn, n):
    cats = ["NA", "PD", "XY"]
    with open(fn, "w") as f:
        f.write("id,PD,x\n")
        for i in range(n):
            f.write(f"{i},{cats[i % 3]},{i*0.5}\n")
for n in (6, 30, 300):
    fn = os.path.join(here, f"na_{n}.csv"); write(fn, n)
    t = Table.from_file(fn)
    var = t.domain["PD"]
    col = t.get_column("PD")
    if var.is_string:
        nmiss = sum(1 for v in col if v == "" )
        vals = sorted(set(col))
    else:
        nmiss = int(np.isnan(col).sum()); vals = var.values
    print(f"n={n}: PD type={type(var).__name__}, values={vals}, missing={nmiss}/{n}")
