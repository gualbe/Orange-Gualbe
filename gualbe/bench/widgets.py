"""Widget-level benchmarks for Orange-Gualbe.

Times how long widgets take from receiving data until their outputs are
ready, as in a workflow (offscreen, no window is shown). Each benchmark is
a test method; results are printed and optionally written as JSON.

Usage:
    QT_QPA_PLATFORM=offscreen BENCH_ROWS=200000 \\
        python -m unittest gualbe/bench/widgets.py
    BENCH_OUT=results.json BENCH_ONLY=group_by,pivot BENCH_PROFILE=10 ...
"""
import cProfile
import json
import os
import pstats
import sys
import time
import unittest

import numpy as np

from Orange.classification import (
    LogisticRegressionLearner, NaiveBayesLearner, TreeLearner
)
from Orange.data import Domain, Table
from Orange.widgets.tests import base as widget_test_base

sys.path.insert(0, os.path.dirname(__file__))
from large_data import make_dense  # pylint: disable=wrong-import-position

ROWS = int(os.environ.get("BENCH_ROWS", 200_000))
ONLY = {s for s in os.environ.get("BENCH_ONLY", "").split(",") if s}
# number of top functions to print from a profile of each benchmark (0: off)
PROFILE = int(os.environ.get("BENCH_PROFILE", 0))
TIMEOUT = 30 * 60 * 1000
RESULTS = {}


def setUpModule():
    print(f"\nwidget benchmarks, rows={ROWS}", flush=True)


def tearDownModule():
    out = os.environ.get("BENCH_OUT")
    if out:
        with open(out, "w") as f:
            json.dump({"meta": {"rows": ROWS}, "results": RESULTS}, f,
                      indent=1)


class BenchWidgets(widget_test_base.WidgetTest):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.data = make_dense(ROWS)
        cls.small = cls.data[:min(ROWS, 5000)]

    def setUp(self):
        name = self._testMethodName[len("test_"):]
        if ONLY and name not in ONLY:
            self.skipTest("not selected")

    def _record(self, name, seconds, error=None, outputs=None):
        RESULTS[name] = {"time": seconds, "outputs": outputs} \
            if error is None else {"error": error}
        msg = f"{seconds:9.3f}s  {outputs}" if error is None \
            else f"ERROR {error}"
        print(f"\nwidget  {name:30s} {msg}", flush=True)

    def _describe_outputs(self, widget):
        # Sizes of outputs, to check that the widget really did the work
        described = {}
        for output in widget.Outputs.__dict__.values():
            if not hasattr(output, "name"):
                continue
            value = self.get_output(output, widget=widget, wait=0)
            if value is None:
                continue
            described[output.name] = \
                f"{type(value).__name__}[{len(value)}]" \
                if hasattr(value, "__len__") else type(value).__name__
        return described

    def _time(self, widget, *signals):
        """Send (signal, value) pairs and wait until outputs are ready"""
        name = self._testMethodName[len("test_"):]
        profiler = cProfile.Profile() if PROFILE else None
        try:
            start = time.perf_counter()
            if profiler:
                profiler.enable()
            for signal, value, *args in signals:
                self.send_signal(signal, value, *args, widget=widget)
            self.wait_until_finished(widget, timeout=TIMEOUT)
            elapsed = time.perf_counter() - start
            if profiler:
                profiler.disable()
                pstats.Stats(profiler).sort_stats("tottime").print_stats(PROFILE)
            self._record(name, elapsed, outputs=self._describe_outputs(widget))
        except Exception as e:  # pylint: disable=broad-except
            self._record(name, None, repr(e)[:200])
            raise

    # --- data -------------------------------------------------------------

    def test_data_table(self):
        from Orange.widgets.data.owtable import OWTable
        w = self.create_widget(OWTable)
        self._time(w, (w.Inputs.data, self.data))

    def test_feature_statistics(self):
        from Orange.widgets.data.owfeaturestatistics import \
            OWFeatureStatistics
        w = self.create_widget(OWFeatureStatistics)
        self._time(w, (w.Inputs.data, self.data))

    def test_group_by(self):
        from Orange.widgets.data.owgroupby import OWGroupBy
        w = self.create_widget(OWGroupBy)
        self._time(w, (w.Inputs.data, self.data))

    def test_pivot(self):
        from Orange.widgets.data.owpivot import OWPivot
        w = self.create_widget(OWPivot)
        self._time(w, (w.Inputs.data, self.data))

    def test_merge_data(self):
        from Orange.widgets.data.owmergedata import OWMergeData
        w = self.create_widget(OWMergeData)
        d = self.data.domain
        perm = np.random.default_rng(0).permutation(len(self.data))
        extra = self.data[perm].transform(
            Domain(d.attributes[:5], None, d.metas))
        self._time(w, (w.Inputs.data, self.data),
                   (w.Inputs.extra_data, extra))

    def test_feature_constructor(self):
        from Orange.widgets.data.owfeatureconstructor import (
            OWFeatureConstructor, ContinuousDescriptor
        )
        descriptors = [
            ContinuousDescriptor("f1", "c0 + c1 * 2", 3, False),
            ContinuousDescriptor("f2", "sqrt(abs(c2)) if c3 > 0 else c4",
                                 3, False)]
        w = self.create_widget(OWFeatureConstructor,
                               stored_settings={"descriptors": descriptors})
        self._time(w, (w.Inputs.data, self.data))

    def test_preprocess(self):
        from Orange.widgets.data.owpreprocess import OWPreprocess
        w = self.create_widget(OWPreprocess, stored_settings={
            "storedsettings": {"preprocessors": [
                ("orange.preprocess.impute", {}),
                ("orange.preprocess.continuize", {}),
                ("orange.preprocess.scale", {})]}})
        self._time(w, (w.Inputs.data, self.data))

    def test_discretize(self):
        from Orange.widgets.data.owdiscretize import (
            OWDiscretize, VarHint, Methods, DefaultKey
        )
        w = self.create_widget(OWDiscretize, stored_settings={
            "var_hints": {DefaultKey: VarHint(Methods.EqualFreq, (4,))},
            "__version__": OWDiscretize.settings_version})
        self._time(w, (w.Inputs.data, self.data))

    def test_continuize(self):
        from Orange.widgets.data.owcontinuize import OWContinuize
        w = self.create_widget(OWContinuize)
        self._time(w, (w.Inputs.data, self.data))

    def test_impute(self):
        from Orange.widgets.data.owimpute import OWImpute, Method
        w = self.create_widget(OWImpute, stored_settings={
            "_default_method_index": int(Method.Average)})
        self._time(w, (w.Inputs.data, self.data))

    def test_data_sampler(self):
        from Orange.widgets.data.owdatasampler import OWDataSampler
        w = self.create_widget(OWDataSampler)
        self._time(w, (w.Inputs.data, self.data))

    def test_unique(self):
        from Orange.widgets.data.owunique import OWUnique
        w = self.create_widget(OWUnique)
        self._time(w, (w.Inputs.data, self.data))

    def test_concatenate(self):
        from Orange.widgets.data.owconcatenate import OWConcatenate
        w = self.create_widget(OWConcatenate)
        self._time(w, (w.Inputs.primary_data, self.data),
                   (w.Inputs.additional_data, self.data))

    def test_correlations(self):
        from Orange.widgets.data.owcorrelations import OWCorrelations
        w = self.create_widget(OWCorrelations)
        self._time(w, (w.Inputs.data, self.data))

    def test_rank(self):
        from Orange.widgets.data.owrank import OWRank
        w = self.create_widget(OWRank)
        self._time(w, (w.Inputs.data, self.data))

    # --- visualize ----------------------------------------------------------

    def test_distributions(self):
        from Orange.widgets.visualize.owdistributions import \
            OWDistributions
        w = self.create_widget(OWDistributions)
        self._time(w, (w.Inputs.data, self.data))

    def test_box_plot(self):
        from Orange.widgets.visualize.owboxplot import OWBoxPlot
        w = self.create_widget(OWBoxPlot)
        self._time(w, (w.Inputs.data, self.data))

    def test_scatter_plot(self):
        from Orange.widgets.visualize.owscatterplot import OWScatterPlot
        w = self.create_widget(OWScatterPlot)
        self._time(w, (w.Inputs.data, self.data))

    # --- unsupervised -------------------------------------------------------

    def test_pca(self):
        from Orange.widgets.unsupervised.owpca import OWPCA
        w = self.create_widget(OWPCA)
        self._time(w, (w.Inputs.data, self.data))

    def test_distances_5k(self):
        from Orange.widgets.unsupervised.owdistances import OWDistances
        w = self.create_widget(OWDistances)
        self._time(w, (w.Inputs.data, self.small))

    # --- evaluate -----------------------------------------------------------

    def test_test_and_score(self):
        from Orange.widgets.evaluate.owtestandscore import OWTestAndScore
        w = self.create_widget(OWTestAndScore)
        self._time(w, (w.Inputs.train_data, self.data),
                   (w.Inputs.learner, NaiveBayesLearner(), 1),
                   (w.Inputs.learner, LogisticRegressionLearner(), 2),
                   (w.Inputs.learner, TreeLearner(max_depth=8), 3))

    def test_predictions(self):
        from Orange.widgets.evaluate.owpredictions import OWPredictions
        w = self.create_widget(OWPredictions)
        model = LogisticRegressionLearner()(self.data)
        self._time(w, (w.Inputs.data, self.data),
                   (w.Inputs.predictors, model))


if __name__ == "__main__":
    unittest.main()
