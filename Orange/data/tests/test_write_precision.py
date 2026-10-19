import os
import shutil
import tempfile
import unittest

import numpy as np

from Orange.data import ContinuousVariable, Domain, Table
from Orange.data.io import TabReader


class TestWritePrecision(unittest.TestCase):
    # gh-6916: values of variables without a set number of decimals were
    # written with "%g", that is, with only six significant digits
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_large_numbers_keep_all_digits(self):
        var = ContinuousVariable("x")
        self.assertEqual(TabReader.format_column(
            var, np.array([-22112215.0, 0.1, 1 / 3, 5.0, 1e-5])),
            ["-22112215", "0.1", "0.3333333333333333", "5", "1e-05"])
        fmt = TabReader.formatter(var)
        self.assertEqual(fmt(-22112215.0), "-22112215")

    def test_fixed_decimals_kept_when_exact(self):
        var = ContinuousVariable("x", number_of_decimals=3)
        self.assertEqual(
            TabReader.format_column(var, np.array([0.5, 1.25, 1 / 3])),
            ["0.500", "1.250", "0.3333333333333333"])

    def test_roundtrip_is_exact(self):
        rng = np.random.default_rng(0)
        values = rng.standard_normal((300, 3)) \
            * 10.0 ** rng.integers(-10, 12, (300, 3))
        values[::7, 0] = np.nan
        domain = Domain([ContinuousVariable("a"),
                         ContinuousVariable("b", number_of_decimals=2),
                         ContinuousVariable("c", number_of_decimals=0)])
        table = Table.from_numpy(domain, values)
        for ext in (".tab", ".csv", ".xlsx"):
            path = os.path.join(self.tmpdir, "data" + ext)
            table.save(path)
            np.testing.assert_array_equal(Table.from_file(path).X, values,
                                          err_msg=ext)


if __name__ == "__main__":
    unittest.main()
