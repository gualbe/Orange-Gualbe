import os
import shutil
import tempfile
import unittest

import numpy as np
import pandas as pd

from Orange.data import ContinuousVariable, StringVariable, Table
from Orange.data.io_util import guess_data_type
from Orange.data.pandas_compat import table_from_frame

IDS = ["10213407285517229", "10155206846088649", "123", "?"]


class TestLargeIntegers(unittest.TestCase):
    # gh-6203: integers above 2 ** 53 (e.g. identifiers) lost digits when
    # they were read as floats
    def test_guess_data_type(self):
        _, values, coltype = guess_data_type(np.array(IDS, dtype=object))
        self.assertIs(coltype, StringVariable)
        self.assertEqual(list(values[:2]), IDS[:2])

        for numbers in (["1", "2", "9007199254740992"],
                        ["100000000000000000000", "3"],  # exact as float
                        ["1e20", "2.5"]):
            _, _, coltype = guess_data_type(np.array(numbers, dtype=object))
            self.assertIs(coltype, ContinuousVariable, numbers)

    def test_read_file(self):
        tmpdir = tempfile.mkdtemp()
        try:
            path = os.path.join(tmpdir, "ids.csv")
            with open(path, "w", encoding="utf-8") as f:
                f.write("id,x\n" + "".join(f"{i},{k}\n"
                                           for k, i in enumerate(IDS[:3])))
            table = Table.from_file(path)
            self.assertIsInstance(table.domain["id"], StringVariable)
            self.assertEqual(list(table.get_column("id")), IDS[:3])
        finally:
            shutil.rmtree(tmpdir)

    def test_table_from_frame(self):
        df = pd.DataFrame({"id": [10213407285517229, 123], "x": [1, 2]})
        table = table_from_frame(df)
        self.assertIsInstance(table.domain["id"], StringVariable)
        self.assertEqual(list(table.get_column("id")),
                         ["10213407285517229", "123"])
        self.assertIsInstance(table.domain["x"], ContinuousVariable)


if __name__ == "__main__":
    unittest.main()
