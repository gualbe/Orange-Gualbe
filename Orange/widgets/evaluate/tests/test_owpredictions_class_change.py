import numpy as np

from Orange.data import Table, Domain, ContinuousVariable, DiscreteVariable
from Orange.regression import LinearRegressionLearner
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.evaluate.owpredictions import OWPredictions


class TestPredictionsClassChange(WidgetTest):
    # gh-6672: shown_probs restored from a context with a discrete class
    # (here without values) was applied to a continuous or missing class
    def setUp(self):
        self.w = self.create_widget(OWPredictions)
        x, y = ContinuousVariable("x"), ContinuousVariable("y")
        X = np.random.default_rng(0).normal(size=(12, 2))
        train = Table.from_numpy(Domain([x, y], ContinuousVariable("z")),
                                 X, X @ [1, 2])
        self.model = LinearRegressionLearner()(train)
        self.no_values = Table.from_numpy(
            Domain([x, y], DiscreteVariable("z", values=())),
            X[:3], np.full(3, np.nan))
        self.continuous = train[:3]
        self.no_class = train[:3].transform(Domain([x, y]))

    def test_discrete_without_values_then_continuous(self):
        self.send_signal(self.w.Inputs.predictors, self.model,
                         widget=self.w)
        self.send_signal(self.w.Inputs.data, self.no_values,
                         widget=self.w)
        self.send_signal(self.w.Inputs.data, self.continuous,
                         widget=self.w)
        self.assertIsNotNone(
            self.get_output(self.w.Outputs.annotated, widget=self.w))

    def test_discrete_without_values_then_no_class(self):
        self.send_signal(self.w.Inputs.predictors, self.model,
                         widget=self.w)
        self.send_signal(self.w.Inputs.data, self.no_values,
                         widget=self.w)
        self.send_signal(self.w.Inputs.data, self.no_class,
                         widget=self.w)
        self.assertIsNotNone(
            self.get_output(self.w.Outputs.annotated, widget=self.w))

    def test_report_without_predictors(self):
        self.send_signal(self.w.Inputs.data, self.continuous,
                         widget=self.w)
        self.w.send_report()
