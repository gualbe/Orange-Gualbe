import unittest
from unittest.mock import Mock, patch

import numpy as np

from Orange.data import ContinuousVariable, Domain, Table
from Orange.data.table import _FromTableConversion


def _table(n_rows, n_cols):
    domain = Domain([ContinuousVariable(f"x{i}") for i in range(n_cols)])
    return Table.from_numpy(domain, np.zeros((n_rows, n_cols)))


class TestConversionBlocks(unittest.TestCase):
    def test_rows_at_once_depends_on_width(self):
        conv = _FromTableConversion.__new__(_FromTableConversion)
        conv.columnwise = []
        cls = _FromTableConversion
        self.assertEqual(conv._rows_at_once(_table(1, 3)),
                         cls.max_rows_at_once)
        self.assertEqual(conv._rows_at_once(_table(1, 100)),
                         cls.max_cells_at_once // 100)
        self.assertEqual(conv._rows_at_once(_table(1, 10000)),
                         cls.min_rows_at_once)

    def test_wide_table_is_converted_in_blocks(self):
        n_cols = 1000
        source = _table(12000, n_cols)
        counter = Mock(side_effect=lambda data: np.ones(len(data)))
        domain = Domain([ContinuousVariable("s", compute_value=counter)])
        with patch.object(_FromTableConversion, "max_cells_at_once",
                          5000 * n_cols):
            result = source.transform(domain)
        np.testing.assert_equal(result.X, 1)
        self.assertEqual([len(call[0][0]) for call in counter.call_args_list],
                         [5000, 5000, 2000])


if __name__ == "__main__":
    unittest.main()
