import os
import shutil
import tempfile
import unittest

import numpy as np
import openpyxl

from Orange.data import Table


class TestExcelEmptyFlagsRow(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _write(self, rows):
        wb = openpyxl.Workbook()
        for row in rows:
            wb.active.append(row)
        path = os.path.join(self.tmpdir, "data.xlsx")
        wb.save(path)
        return path

    def test_three_line_header_without_flags(self):
        # gh-7276: the empty flags row was dropped, so the header was misread
        path = self._write([["a", "b"], ["continuous", "continuous"],
                            [None, None], [1, 2], [None, None], [3, 4]])
        table = Table.from_file(path)
        self.assertEqual([v.name for v in table.domain.attributes], ["a", "b"])
        self.assertIsNone(table.domain.class_var)
        np.testing.assert_equal(table.X, [[1, 2], [3, 4]])

    def test_empty_rows_are_skipped(self):
        path = self._write([[None, None], ["a", "b"], [1, 2], [None, None],
                            [3, 4]])
        table = Table.from_file(path)
        np.testing.assert_equal(table.X, [[1, 2], [3, 4]])


if __name__ == "__main__":
    unittest.main()
