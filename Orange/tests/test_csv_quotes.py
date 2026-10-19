import os
import shutil
import tempfile
import unittest

from Orange.data import Table


class TestCSVQuotes(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def _read(self, name, content):
        path = os.path.join(self.tmpdir, name)
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        return Table.from_file(path)

    def test_apostrophes_are_not_quotes(self):
        # gh-6067: the sniffer took "'" as the quote character and an
        # unclosed apostrophe swallowed the following rows
        texts = ["'Hello there'", "A plain sentence.", "It's fine.",
                 "'Tis the season", "Another one", "Last one"]
        table = self._read(
            "data.tab",
            "id\ttext\ncontinuous\tstring\n\tmeta\n"
            + "".join(f"{i}\t{t}\n" for i, t in enumerate(texts)))
        self.assertEqual(len(table), len(texts))
        self.assertEqual(list(table.get_column("text")), texts)

    def test_double_quotes(self):
        table = self._read("data.csv",
                           'a,b\n1,"x, y"\n2,"say ""hi"""\n3,z\n')
        self.assertEqual(list(table.metas[:, 0]), ["x, y", 'say "hi"', "z"])


if __name__ == "__main__":
    unittest.main()
