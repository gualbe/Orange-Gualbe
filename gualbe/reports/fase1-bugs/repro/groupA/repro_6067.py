import os, csv
from Orange.data import Table
here = os.path.dirname(os.path.abspath(__file__))
rows = [
    ("1", "'Hello there'", ),           # cell starts+ends with ' -> sniffer picks '
    ("2", "A plain sentence."),
    ("3", "It's fine."),
    ("4", "'Tis the season to be jolly"),   # leading apostrophe, no closing
    ("5", "Another sentence, ok"),
    ("6", "Last one"),
]
fn = os.path.join(here, "quote_apos.tab")
with open(fn, "w", newline="") as f:
    f.write("id\ttext\ncontinuous\tstring\n\tmeta\n")
    for r in rows:
        f.write("\t".join(r) + "\n")
sample = open(fn).read()
d = csv.Sniffer().sniff("".join(open(fn).readlines()[:10]), "\t")
print("sniffed quotechar:", repr(d.quotechar))
t = Table.from_file(fn)
print("n rows:", len(t), "expected", len(rows))
for (i, txt), r in zip(rows, t):
    got = str(r["text"])
    print(f"  {i}: file={txt!r:40} read={got!r}", "" if got == txt else "  <-- DIFFERS")
