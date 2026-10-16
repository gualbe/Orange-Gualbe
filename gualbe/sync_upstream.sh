#!/usr/bin/env bash
# Bring official Orange (biolab/orange3) changes into Orange-Gualbe.
#
#   gualbe/sync_upstream.sh            # merge upstream/master into gualbe
#   gualbe/sync_upstream.sh 3.41.0     # merge an official release tag instead
#
# Steps: fetch upstream, fast-forward local and remote `master` to it, merge the
# requested ref into `gualbe`, rebuild Cython extensions and run the test
# suite. Nothing is pushed to `gualbe` here: push it yourself once the tests
# and benchmarks look right.
set -euo pipefail

REF="${1:-upstream/master}"
PY="${ORANGE_PY:-$HOME/miniforge3/envs/orange-gualbe/bin/python}"
cd "$(git rev-parse --show-toplevel)"

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
    echo "Working tree has uncommitted changes; commit or stash them first." >&2
    exit 1
fi

git fetch upstream --tags
git switch master
git merge --ff-only upstream/master
git push origin master --tags

git switch gualbe
if ! git merge --no-edit "$REF"; then
    echo "Merge conflicts: resolve them, commit, then rerun the tests." >&2
    exit 1
fi

"$PY" -m pip install -e . --no-build-isolation --no-deps -q
QT_QPA_PLATFORM=offscreen "$PY" -m unittest Orange.tests Orange.widgets.tests 2>&1 \
    | tail -n 3
echo "Merged $REF into gualbe. Next: run gualbe/bench/large_data.py, then git push."
