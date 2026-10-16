"""Large-data benchmarks for Orange-Gualbe.

Times core operations that dominate workflows on big tables (loading,
selecting, transforming, preprocessing, statistics, modelling). Data are
generated in memory; files written by I/O benchmarks go to a temporary
directory that is removed at the end.

Usage:
    python gualbe/bench/large_data.py --rows 1000000 --out results.json
    python gualbe/bench/large_data.py --rows 100000 --only csv,normalize
    python gualbe/bench/compare.py before.json after.json
"""
import argparse
import gc
import json
import os
import pickle
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc

import numpy as np
import scipy.sparse as sp

from Orange.data import (
    ContinuousVariable, DiscreteVariable, Domain, StringVariable, Table
)
from Orange.data import filter as data_filter
from Orange.data.pandas_compat import table_from_frame, table_to_frame
from Orange.statistics.basic_stats import DomainBasicStats
from Orange.statistics.contingency import get_contingencies
from Orange.statistics.distribution import get_distributions
from Orange import preprocess
from Orange.preprocess import discretize
from Orange.distance import Euclidean
from Orange.classification import (
    LogisticRegressionLearner, NaiveBayesLearner, TreeLearner,
    RandomForestLearner, KNNLearner
)
from Orange.clustering import KMeans
from Orange.evaluation import CrossValidation

BENCHES = []


def bench(name, group, repeat=3):
    def decorator(func):
        BENCHES.append((name, group, repeat, func))
        return func
    return decorator


def make_dense(rows, n_cont=40, n_disc=10, missing=0.02, seed=0):
    rng = np.random.default_rng(seed)
    cont = rng.standard_normal((rows, n_cont))
    disc = rng.integers(0, 5, (rows, n_disc)).astype(float)
    X = np.hstack([cont, disc])
    X[rng.random(X.shape) < missing] = np.nan
    y = (cont[:, 0] + cont[:, 1] > 0).astype(float)
    metas = np.array([f"id{i}" for i in range(rows)], dtype=object)[:, None]
    domain = Domain(
        [ContinuousVariable(f"c{i}") for i in range(n_cont)]
        + [DiscreteVariable(f"d{i}", values=tuple("abcde"))
           for i in range(n_disc)],
        DiscreteVariable("y", values=("no", "yes")),
        [StringVariable("id")])
    return Table.from_numpy(domain, X, y, metas)


def make_sparse(rows, cols=2000, density=0.005, seed=0):
    X = sp.random(rows, cols, density=density, format="csr",
                  random_state=seed)
    y = np.random.default_rng(seed).integers(0, 2, rows).astype(float)
    domain = Domain(
        [ContinuousVariable(f"w{i}", sparse=True) for i in range(cols)],
        DiscreteVariable("y", values=("no", "yes")))
    return Table.from_numpy(domain, X, y)


class Ctx:
    def __init__(self, rows, tmpdir):
        self.rows = rows
        self.tmp = tmpdir
        self.data = make_dense(rows)
        self.small = self.data[:min(rows, 20000)]
        self.sparse = make_sparse(max(rows // 10, 1000))
        self.csv = os.path.join(tmpdir, "data.tab")
        self.data.save(self.csv)


# --- construction and I/O ---------------------------------------------------

@bench("from_numpy", "construct")
def _(c):
    d = c.data
    Table.from_numpy(d.domain, d.X, d.Y, d.metas)


@bench("copy", "construct")
def _(c):
    c.data.copy()


@bench("pickle_roundtrip", "io")
def _(c):
    pickle.loads(pickle.dumps(c.data, protocol=pickle.HIGHEST_PROTOCOL))


@bench("tab_write", "io", repeat=1)
def _(c):
    c.data.save(os.path.join(c.tmp, "out.tab"))


@bench("tab_read", "io", repeat=1)
def _(c):
    Table.from_file(c.csv)


@bench("csv_write", "io", repeat=1)
def _(c):
    c.data.save(os.path.join(c.tmp, "out.csv"))


@bench("to_pandas", "io")
def _(c):
    table_to_frame(c.data, include_metas=True)


@bench("from_pandas", "io", repeat=1)
def _(c):
    table_from_frame(table_to_frame(c.data))


# --- selection and transformation -------------------------------------------

@bench("rows_bool_mask", "select")
def _(c):
    c.data[c.data.X[:, 0] > 0]


@bench("rows_random_idx", "select")
def _(c):
    idx = np.random.default_rng(1).permutation(len(c.data))[:len(c.data) // 2]
    c.data[idx]


@bench("select_columns", "select")
def _(c):
    d = c.data.domain
    c.data.transform(Domain(d.attributes[::2], d.class_vars, d.metas))


@bench("filter_values", "select")
def _(c):
    f = data_filter.Values([
        data_filter.FilterContinuous(0, data_filter.FilterContinuous.Greater,
                                     0),
        data_filter.FilterDiscrete(c.data.domain["d0"], [0, 1])])
    f(c.data)


@bench("concatenate_rows", "select")
def _(c):
    Table.concatenate([c.data, c.data])


@bench("transform_sparse_add_col", "select")
def _(c):
    d = c.sparse.domain
    c.sparse.transform(Domain(d.attributes + (ContinuousVariable("x"),),
                              d.class_vars))


# --- statistics ---------------------------------------------------------------

@bench("basic_stats", "stats")
def _(c):
    DomainBasicStats(c.data, include_metas=False)


@bench("distributions", "stats")
def _(c):
    get_distributions(c.data)


@bench("contingencies", "stats")
def _(c):
    get_contingencies(c.data)


# --- preprocessing --------------------------------------------------------------

@bench("impute_average", "preprocess")
def _(c):
    preprocess.Impute()(c.data)


@bench("normalize", "preprocess")
def _(c):
    preprocess.Normalize()(c.data)


@bench("continuize", "preprocess")
def _(c):
    preprocess.Continuize()(c.data)


@bench("discretize_eqfreq", "preprocess")
def _(c):
    preprocess.Discretize(method=discretize.EqualFreq(n=4))(c.data)


@bench("pipeline_impute_cont_norm", "preprocess")
def _(c):
    d = preprocess.Impute()(c.data)
    d = preprocess.Continuize()(d)
    preprocess.Normalize()(d)


# --- modelling ------------------------------------------------------------------

@bench("euclidean_5k", "model")
def _(c):
    Euclidean(c.small[:5000])


@bench("naive_bayes_fit_predict", "model")
def _(c):
    NaiveBayesLearner()(c.data)(c.data)


@bench("logreg_fit_predict", "model", repeat=1)
def _(c):
    LogisticRegressionLearner()(c.data)(c.data)


@bench("tree_fit_20k", "model", repeat=1)
def _(c):
    TreeLearner()(c.small)


@bench("random_forest_20k", "model", repeat=1)
def _(c):
    RandomForestLearner(n_estimators=20, random_state=0)(c.small)


@bench("knn_predict_20k", "model", repeat=1)
def _(c):
    KNNLearner()(c.small)(c.small[:2000])


@bench("kmeans_k5", "model", repeat=1)
def _(c):
    KMeans(n_clusters=5, random_state=0)(preprocess.Impute()(c.data))


@bench("cv5_naive_bayes", "model", repeat=1)
def _(c):
    CrossValidation(k=5)(c.data, [NaiveBayesLearner()])


def run_one(func, ctx, repeat, mem):
    times = []
    for _ in range(repeat):
        gc.collect()
        t0 = time.perf_counter()
        func(ctx)
        times.append(time.perf_counter() - t0)
    peak = None
    if mem:
        gc.collect()
        tracemalloc.start()
        func(ctx)
        peak = tracemalloc.get_traced_memory()[1] / 2 ** 20
        tracemalloc.stop()
    return min(times), peak


def git_rev():
    try:
        return subprocess.check_output(
            ["git", "describe", "--always", "--dirty"],
            cwd=os.path.dirname(__file__), text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=200_000)
    ap.add_argument("--only", default="",
                    help="comma-separated bench names or groups")
    ap.add_argument("--mem", action="store_true",
                    help="also measure peak traced memory (slower)")
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    only = {s for s in args.only.split(",") if s}

    tmpdir = tempfile.mkdtemp(prefix="orange_bench_")
    results = {"meta": {"rows": args.rows, "rev": git_rev(),
                        "python": platform.python_version(),
                        "numpy": np.__version__,
                        "machine": platform.platform(),
                        "date": time.strftime("%Y-%m-%d %H:%M:%S")},
               "results": {}}
    try:
        t0 = time.perf_counter()
        ctx = Ctx(args.rows, tmpdir)
        print(f"setup: {time.perf_counter() - t0:.2f}s "
              f"(rows={args.rows}, rev={results['meta']['rev']})", flush=True)
        for name, group, repeat, func in BENCHES:
            if only and name not in only and group not in only:
                continue
            try:
                t, peak = run_one(func, ctx, repeat, args.mem)
                results["results"][name] = {"group": group, "time": t,
                                            "peak_mb": peak}
                mem = f"  peak {peak:8.1f} MB" if peak is not None else ""
                print(f"{group:10s} {name:28s} {t:9.4f}s{mem}", flush=True)
            except Exception as e:  # pylint: disable=broad-except
                results["results"][name] = {"group": group,
                                            "error": repr(e)}
                print(f"{group:10s} {name:28s} ERROR {e!r}", flush=True)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
