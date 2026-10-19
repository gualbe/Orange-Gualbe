import os
from Orange.data import Table, Domain
from Orange.data.io import ExcelReader
here = os.path.dirname(os.path.abspath(__file__))
iris = Table("iris")[::30]
noclass = iris.transform(Domain(iris.domain.attributes))
fn = os.path.join(here, "iris_noclass.xlsx")
ExcelReader.write_file(fn, noclass, with_annotations=True)
import openpyxl
ws = openpyxl.load_workbook(fn).active
for row in ws.iter_rows(max_row=4, values_only=True):
    print("RAW:", row)
t = Table.from_file(fn)
print("domain:", t.domain, "attrs:", t.domain.attributes, "metas:", t.domain.metas)
print(t[:3])
print("n rows read:", len(t), "expected:", len(noclass))
# control: with class
fn2 = os.path.join(here, "iris_class.xlsx")
ExcelReader.write_file(fn2, iris, with_annotations=True)
t2 = Table.from_file(fn2)
print("control domain:", t2.domain, len(t2))
