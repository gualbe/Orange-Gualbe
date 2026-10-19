import os, csv
from unittest.mock import patch
from Orange.data import Table
here = os.path.dirname(os.path.abspath(__file__))
orig = csv.Sniffer.sniff
def sniff(self, sample, delimiters=None):
    d = orig(self, sample, delimiters)
    if d.quotechar != '"':
        d.quotechar = '"'; d.doublequote = True
    return d
with patch.object(csv.Sniffer, "sniff", sniff):
    t = Table.from_file(os.path.join(here, "quote_apos.tab"))
    print(len(t), [str(r["text"]) for r in t])
