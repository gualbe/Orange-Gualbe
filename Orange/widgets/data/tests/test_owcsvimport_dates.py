import unittest

import pandas as pd

from Orange.widgets.data.owcsvimport import consistent_datetime, guess_data_type


class TestConsistentDates(unittest.TestCase):
    # gh-6499: dates were parsed one by one, so 08/03/18 was read as
    # month-first and 28/03/18 as day-first in the same column
    def test_day_first_when_month_first_does_not_fit(self):
        for values in (["08/03/18", "28/03/18", "01/12/19"],
                       ["28/03/18", "08/03/18", "01/12/19"]):
            parsed = guess_data_type(pd.Series(values, dtype=object))
            self.assertEqual(
                sorted(parsed.dt.strftime("%Y-%m-%d")),
                ["2018-03-08", "2018-03-28", "2019-12-01"], values)

    def test_month_first_when_both_fit(self):
        parsed = consistent_datetime(pd.Series(["08/03/18", "01/12/19"]))
        self.assertEqual(list(parsed.dt.strftime("%Y-%m-%d")),
                         ["2018-08-03", "2019-01-12"])

    def test_iso_and_missing(self):
        parsed = consistent_datetime(
            pd.Series(["2020-01-31", None, "2021-12-01"], dtype=object))
        self.assertEqual(parsed.iloc[0], pd.Timestamp("2020-01-31"))
        self.assertTrue(pd.isna(parsed.iloc[1]))

    def test_not_dates(self):
        self.assertIsNone(consistent_datetime(pd.Series(["a", "b"])))
        self.assertIsNone(consistent_datetime(pd.Series([None, ""])))


if __name__ == "__main__":
    unittest.main()
