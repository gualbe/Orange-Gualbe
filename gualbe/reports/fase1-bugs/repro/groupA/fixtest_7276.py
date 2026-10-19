import os
from itertools import islice, chain
from Orange.data import Table
from Orange.data.io import ExcelReader
here = os.path.dirname(os.path.abspath(__file__))
def get_cells(self):
    def str_(x):
        return str(x) if x is not None and x not in ExcelReader.ERRORS else ""
    sheet = self._get_active_sheet()
    cells = ([str_(c.value) for c in row[sheet.min_column - 1: sheet.max_column]]
             for row in sheet.iter_rows(sheet.min_row, sheet.max_row + 1))
    cells = filter(any, cells) if False else cells
    rows = list(cells)
    # keep only an empty 3rd row when row 2 looks like a type row
    from Orange.data.io_base import _TableHeader
    if len(rows) >= 3 and not any(rows[2]) and _TableHeader.is_type_annotation(rows[1]) if hasattr(_TableHeader,'is_type_annotation') else False:
        pass
    return chain(rows[:3], filter(any, rows[3:]))
ExcelReader.get_cells = get_cells
for f in ("iris_noclass.xlsx", "iris_class.xlsx"):
    t = Table.from_file(os.path.join(here, f)); print(f, t.domain, len(t))
# plain file w/o header annotations and an empty row 3
import openpyxl
wb = openpyxl.Workbook(); ws = wb.active
ws.append(["a", "b"]); ws.append([1, 2]); ws.append([None, None]); ws.append([3, 4])
fn = os.path.join(here, "plain_emptyrow3.xlsx"); wb.save(fn)
t = Table.from_file(fn); print("plain with empty row 3:", t.domain, len(t), t.X.tolist())
