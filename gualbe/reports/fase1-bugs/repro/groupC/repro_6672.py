import unittest, traceback, numpy as np
from Orange.data import Table, Domain, ContinuousVariable, DiscreteVariable
from Orange.regression import LinearRegressionLearner
from Orange.classification import LogisticRegressionLearner
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.evaluate.owpredictions import OWPredictions

x, y, z = (ContinuousVariable(n) for n in "xyz")
rng = np.random.default_rng(0)
X = rng.normal(size=(12, 2)); Y = X @ [1, 2] + 0.1
train = Table.from_numpy(Domain([x, y], z), X, Y)

class T(WidgetTest):
    def run_case(self, name, steps):
        w = self.create_widget(OWPredictions)
        try:
            for sig, val in steps:
                self.send_signal(getattr(w.Inputs, sig), val, widget=w)
            print(f"[OK]   {name}")
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)[-1]
            print(f"[FAIL] {name}: {type(e).__name__}: {e} @ {tb.name}:{tb.lineno}")
        return w

    def test_cases(self):
        reg = LinearRegressionLearner()(train)
        iris = Table("iris")
        clf = LogisticRegressionLearner()(iris)
        # 1. test data with target all missing ("?")
        t1 = Table.from_numpy(Domain([x, y], z), X[:3], np.full(3, np.nan))
        self.run_case("reg model + all-missing continuous target", [("predictors", reg), ("data", t1)])
        # 2. test data without class var
        t2 = Table.from_numpy(Domain([x, y]), X[:3])
        self.run_case("reg model + no class var", [("predictors", reg), ("data", t2)])
        # 3. target column of all "?" inferred as discrete w/o values (as File would do)
        zd = DiscreteVariable("z", values=())
        t3 = Table.from_numpy(Domain([x, y], zd), X[:3], np.full(3, np.nan))
        self.run_case("reg model + discrete target with no values", [("predictors", reg), ("data", t3)])
        # 4. classification predictor on regression data
        self.run_case("clf model + regression data (housing)", [("predictors", clf), ("data", Table("housing"))])
        # 5. regression predictor on classification data
        self.run_case("reg model + iris", [("predictors", reg), ("data", iris)])
        # 6. switching data: discrete-no-values then continuous / no class in same widget
        self.run_case("discrete-no-values -> continuous target (same widget)",
                      [("predictors", reg), ("data", t3), ("data", t1)])
        self.run_case("discrete-no-values -> no class var (same widget)",
                      [("predictors", reg), ("data", t3), ("data", t2)])
        # 7. iris + clf, then housing + reg replacing
        self.run_case("iris/clf -> housing/reg",
                      [("predictors", clf), ("data", iris), ("data", Table("housing"))])
        # 8. data first, then predictor removed
        w = self.run_case("predictor then data None", [("predictors", reg), ("data", t1), ("data", None)])



class R(WidgetTest):
    def test_report(self):
        reg = LinearRegressionLearner()(train)
        for steps in ([], [("predictors", reg)], [("data", train)], [("predictors", reg), ("data", train), ("data", None)]):
            w = self.create_widget(OWPredictions)
            for s, v in steps:
                self.send_signal(getattr(w.Inputs, s), v, widget=w)
            try:
                w.send_report(); print("[OK]   report", [s for s, _ in steps])
            except Exception as e:
                tb = traceback.extract_tb(e.__traceback__)[-1]
                print(f"[FAIL] report {[s for s,_ in steps]}: {type(e).__name__}: {e} @ {tb.name}:{tb.lineno}")
unittest.main()
