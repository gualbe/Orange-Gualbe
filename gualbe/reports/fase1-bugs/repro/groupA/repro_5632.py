import unittest
import scipy.sparse as sp
from Orange.data import Table, Domain
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.data.owmergedata import OWMergeData

def kinds(t):
    return {k: ("sparse" if sp.issparse(getattr(t, k)) else "dense") + str(getattr(t, k).shape)
            for k in ("X", "Y", "metas")}

class T(WidgetTest):
    def test_issue(self):
        self.widget = w = self.create_widget(OWMergeData)
        data = Table("iris")[::25]
        ed = Table("titanic")[::300].to_sparse()
        self.send_signal(w.Inputs.data, data); self.send_signal(w.Inputs.extra_data, ed)
        out = self.get_output(w.Outputs.data)
        print("\nmerge output:", kinds(out), "domain attrs:", len(out.domain.attributes))
        c = out.copy(); print("copy        :", kinds(c))

    def test_direct(self):
        t = Table("titanic")[::300].to_sparse()
        print("\ntitanic sparse:", kinds(t), "-> copy:", kinds(t.copy()))
        # sparse X with zero columns / one row etc.
        z = t.transform(Domain([], t.domain.class_var))
        z = z.to_sparse()
        print("no attrs sparse:", kinds(z), "-> copy:", kinds(z.copy()))
        # table whose X is sparse but empty columns subset like merge output
        import numpy as np
        X = sp.csr_matrix(np.zeros((3, 2)))
        dom = Domain([t.domain.attributes[0], t.domain.attributes[1]])
        tt = Table.from_numpy(dom, X)
        print("all-zero sparse X:", kinds(tt), "-> copy:", kinds(tt.copy()))

if __name__ == "__main__":
    unittest.main()
