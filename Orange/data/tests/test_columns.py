import unittest

import numpy as np

from Orange.data import _columns
from Orange.data.variable import MISSING_VALUES

NA_STRINGS = {v for v in MISSING_VALUES if isinstance(v, str)}


class TestParseContinuous(unittest.TestCase):
    def test_matches_float(self):
        cases = ["1.5", " 1.5", "1.5 ", "1_000", "inf", "-Infinity", "NaN",
                 "1e5", "1E-3", "-0", "+.5", "５.５", "1.5\n", "5.", ".5",
                 "1e400", "-1e-400", "00012", "4.9e-324",
                 "123456789012345678901234567890", "0." + "1" * 30]
        floats, namask, bad = _columns.parse_continuous(
            np.array(cases, dtype=object), NA_STRINGS)
        self.assertEqual(bad, -1)
        self.assertFalse(namask.any())
        expected = np.array([float(c) for c in cases])
        np.testing.assert_array_equal(floats, expected)
        np.testing.assert_array_equal(np.signbit(floats),
                                      np.signbit(expected))

    def test_missing(self):
        floats, namask, bad = _columns.parse_continuous(
            np.array(["?", "1", "", "NA", "~", "nan", ".", "2"],
                     dtype=object), NA_STRINGS)
        self.assertEqual(bad, -1)
        np.testing.assert_array_equal(
            namask, [True, False, True, True, True, True, True, False])
        np.testing.assert_array_equal(floats[~namask], [1, 2])
        self.assertTrue(np.isnan(floats[namask]).all())

    def test_invalid(self):
        for invalid in ("0x10", "abc", "1,5", "1.2.3", "  ", "-", "-.", "1e",
                        "1e+", "--1", "1-"):
            _, _, bad = _columns.parse_continuous(
                np.array(["1", "?", invalid, "abc"], dtype=object),
                NA_STRINGS)
            self.assertEqual(bad, 2, invalid)

    def test_empty(self):
        floats, namask, bad = _columns.parse_continuous(
            np.array([], dtype=object), NA_STRINGS)
        self.assertEqual((floats.shape, namask.shape, bad), ((0,), (0,), -1))


class TestMaxDecimals(unittest.TestCase):
    def test_max_decimals(self):
        def reference(values):
            return max((len(v) - v.find(".") for v in values if "." in v),
                       default=1) - 1

        for values in ([], ["1", "2"], ["1.", "?"], ["1.25", "3.1", "1.2.3"],
                       ["a.bcd", "x"], ["é.ñ", "."], ["0.000001", "1e-5"]):
            arr = np.array(values, dtype=object)
            self.assertEqual(_columns.max_decimals(arr), reference(values),
                             values)

    def test_non_strings(self):
        self.assertRaises(TypeError, _columns.max_decimals,
                          np.array(["1.5", 2.5], dtype=object))


class TestStripRows(unittest.TestCase):
    def test_strip_rows(self):
        rows = [["a ", " b", "c"], ["", "", ""], ["\td\n", "e"],
                ["x", "y", "z", "w"], []]
        stripped, truncated = _columns.strip_rows(iter(rows), 3)
        self.assertEqual(stripped, [["a", "b", "c"], ["d", "e", ""],
                                    ["x", "y", "z"]])
        self.assertTrue(truncated)

        stripped, truncated = _columns.strip_rows(iter(rows[:3]), 0)
        self.assertEqual(stripped, [["a", "b", "c"], ["d", "e"]])
        self.assertFalse(truncated)

    def test_keeps_unchanged_objects(self):
        value = "abc"
        (row,), _ = _columns.strip_rows([[value]], 1)
        self.assertIs(row[0], value)


class TestMergeCounts(unittest.TestCase):
    def test_merge_counts(self):
        values, counts = _columns.merge_counts([
            np.array([1., 1, 3]), np.array([]), np.array([-np.inf, 1, 2, 3, 3]),
            np.array([0., np.inf])])
        np.testing.assert_array_equal(values, [-np.inf, 0, 1, 2, 3, np.inf])
        np.testing.assert_array_equal(counts, [[0, 0, 2, 0, 1, 0],
                                               [0, 0, 0, 0, 0, 0],
                                               [1, 0, 1, 1, 2, 0],
                                               [0, 1, 0, 0, 0, 1]])

    def test_empty(self):
        values, counts = _columns.merge_counts([])
        self.assertEqual((values.shape, counts.shape), ((0,), (0, 0)))
        values, counts = _columns.merge_counts([np.array([]), np.array([])])
        self.assertEqual((values.shape, counts.shape), ((0,), (2, 0)))


if __name__ == "__main__":
    unittest.main()
