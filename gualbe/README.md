# Orange-Gualbe

A distribution of [Orange](https://github.com/biolab/orange3) focused on
speed and robustness with large data. It follows the official repository and
adds performance and stability patches on top.

Licensed like Orange: GPL-3.0-or-later.

## Branches

| Branch    | Contents                                                        |
|-----------|-----------------------------------------------------------------|
| `master`  | Exact copy of `biolab/orange3` master; never committed to here. |
| `gualbe`  | Default branch: upstream + Orange-Gualbe patches.               |
| `perf/*`, `fix/*` | One change each; merged into `gualbe` when tested.      |

Versions are tagged as `<upstream version>+gualbe.<n>`, e.g. `3.41.0+gualbe.1`.

## Setup (macOS / conda)

```bash
conda create -n orange-gualbe -c conda-forge python=3.12 "numpy<2.4" scipy \
    scikit-learn "pandas<3" bottleneck cython "pyqt=5.15" pyqtwebengine anyqt \
    matplotlib pyqtgraph qtconsole openpyxl xlrd xlsxwriter networkx opentsne \
    python-louvain "xgboost<2.1"
conda activate orange-gualbe
pip install -e . --no-build-isolation
python -m Orange.canvas          # start the GUI
```

## Verification (local, no CI)

```bash
QT_QPA_PLATFORM=offscreen python -m unittest Orange.tests Orange.widgets.tests
python gualbe/bench/large_data.py --rows 1000000 --out after.json
python gualbe/bench/compare.py gualbe/bench/results/baseline-1M.json after.json
```

Every patch must keep the test suite at the baseline and show a measured
improvement (or no regression) in the benchmarks. Baseline results are in
`gualbe/bench/results/`.

## Updating from the official repository

```bash
gualbe/sync_upstream.sh            # latest upstream master
gualbe/sync_upstream.sh 3.41.0     # or a specific release tag
```

## Changes

See [CHANGELOG.md](CHANGELOG.md).
