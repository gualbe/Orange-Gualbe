# Orange-Gualbe changelog

Changes on top of upstream Orange. Each entry: what changed, why, and the
measured effect (benchmark name, rows, before → after). Timings are from
`gualbe/bench/large_data.py` on an Apple M4 Max; results files are in
`gualbe/bench/results/`.

## Unreleased

Base: upstream master `bd6fef4ca` (3.41.0.dev, after 3.40.0).

### Performance

- **Writing .tab/.csv** — values are formatted per column (floats in
  Cython via `PyOS_double_to_string`, discrete values by indexing) in
  blocks of 10,000 rows. Output is byte-for-byte identical; peak memory
  stays ~45 MB regardless of size.
  1M rows × 52 columns: `tab_write` 25.3 s → 7.7 s (3.3×),
  `csv_write` 25.6 s → 7.4 s (3.5×).
- **Reading .tab/.csv** — continuous columns are parsed, missing values
  detected and decimals counted in single-pass Cython loops
  (`Orange/data/_columns.pyx`) with unchanged semantics; the cyclic GC is
  paused while row lists are built; UTF-8 is tried before ASCII, so UTF-8
  files with accents (ñ, á, …) are no longer parsed twice.
  1M rows: `tab_read` 21.0 s → 10.9 s (1.9×); 500k-row UTF-8 file with
  one non-ASCII value 7.1 s → 4.0 s.
- **Contingencies of continuous variables** (Box Plot, Distributions,
  Naive Bayes, Rank, …) — values of each class are sorted separately and
  merged in one linear pass instead of an indirect sort of the column.
  Identical results. 1M rows: `contingencies` 9.4 s → 3.0 s (3.1×).

### Fixes

- `Table._compute_contingency` crashed with `IndexError` (or used wrong
  weights) on sparse data with instance weights and more than one
  continuous column.

### Tooling

- Large-data benchmark suite (`gualbe/bench/`) and upstream sync script
  (`gualbe/sync_upstream.sh`).
