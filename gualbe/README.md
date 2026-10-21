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
    "scikit-learn<1.11" "pandas<3" bottleneck cython "pyqt=5.15" pyqtwebengine anyqt \
    matplotlib pyqtgraph qtconsole openpyxl xlrd xlsxwriter networkx opentsne \
    python-louvain "xgboost<2.1" "libblas=*=*accelerate"   # Accelerate BLAS on Apple Silicon
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

## Release binaries

GitHub Actions is used only to build release binaries (public repositories do
not consume Actions minutes); inherited upstream workflows are disabled.

1. Tag the release on `gualbe` (e.g. `3.41.0+gualbe.2`) and publish a GitHub
   release with notes from `gualbe/releases/`.
2. Wheels for Linux, macOS and Windows (Python 3.11-3.14), attached to the
   release automatically:
   `gh workflow run "Orange-Gualbe wheels" -R gualbe/Orange-Gualbe --ref gualbe -f tag=<tag>`
3. Installers from [gualbe/Orange-Gualbe-installers](https://github.com/gualbe/Orange-Gualbe-installers)
   (branch `orange-gualbe`), each tested by running the full test suite on
   the installed app:
   `gh workflow run "Build Windows Installer" -R gualbe/Orange-Gualbe-installers --ref orange-gualbe -f tag=<tag>`
   `gh workflow run "Build macOS dmg" -R gualbe/Orange-Gualbe-installers --ref orange-gualbe -f tag=<tag>`
   then download the artifacts (`gh run download`) and attach them with
   `gh release upload`.

