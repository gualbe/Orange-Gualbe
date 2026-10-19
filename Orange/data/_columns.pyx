#cython: language_level=3
#cython: boundscheck=False
#cython: wraparound=False
"""
Single-pass helpers for converting columns of strings read from text files.

They do the same as the corresponding Python code in io_base and io_util, but
avoid creating Python-level frames and temporary arrays for each value.
"""

import numpy as np
cimport numpy as np

from cpython.unicode cimport PyUnicode_Check, PyUnicode_GET_LENGTH
from cpython.set cimport PySet_Contains
from cpython.ref cimport PyObject
from libc.math cimport INFINITY

np.import_array()


cdef extern from "Python.h":
    Py_ssize_t PyUnicode_FindChar(object s, Py_UCS4 ch, Py_ssize_t start,
                                  Py_ssize_t end, int direction) except -2


def parse_continuous(values, set na_strings):
    """
    Convert an object array of strings to floats.

    Strings in `na_strings` become nan. Other values are converted with
    `float`.

    Returns:
        (floats, namask, bad): `bad` is the index of the first value that
        cannot be converted (in which case `floats` is incomplete) or -1.
    """
    cdef:
        np.ndarray[np.float64_t, ndim=1] floats
        np.ndarray[np.uint8_t, ndim=1, cast=True] namask
        np.ndarray[object, ndim=1] arr = np.asarray(values, dtype=object)
        Py_ssize_t i, n = arr.shape[0]
        object value
        double nan = np.nan

    floats = np.empty(n, dtype=np.float64)
    namask = np.zeros(n, dtype=bool)
    for i in range(n):
        value = arr[i]
        if PySet_Contains(na_strings, value) == 1:
            namask[i] = True
            floats[i] = nan
        elif not _fast_float(value, &floats[i]):
            try:
                floats[i] = float(value)
            except (ValueError, TypeError):
                return floats, namask, i
    return floats, namask, -1


cdef extern from "Python.h":
    int PyUnicode_IS_COMPACT_ASCII(object s)
    void *PyUnicode_DATA(object s)
    double PyOS_string_to_double(const char *s, char **endptr,
                                 PyObject *overflow_exception)
    PyObject *PyErr_Occurred()
    void PyErr_Clear()


cdef inline bint _fast_float(object value, double *result):
    # Parse a compact ASCII string that consists of a number only; return
    # False for anything else (whitespace, underscores, non-ASCII, errors),
    # which the caller then passes to `float` for exact Python semantics
    cdef:
        Py_ssize_t i, length
        const char *start
        char *end
        char c
    if not PyUnicode_Check(value) or not PyUnicode_IS_COMPACT_ASCII(value):
        return False
    length = PyUnicode_GET_LENGTH(value)
    if length == 0 or length > 64:
        return False
    start = <const char *>PyUnicode_DATA(value)
    c = start[0]
    if not (c == b'-' or c == b'+' or c == b'.' or b'0' <= c <= b'9'):
        return False
    c = start[length - 1]
    if not (c == b'.' or b'0' <= c <= b'9'):
        return False
    for i in range(length):
        if start[i] == b'_':
            return False
    result[0] = PyOS_string_to_double(start, &end, NULL)
    if PyErr_Occurred() != NULL:
        PyErr_Clear()
        return False
    return end == start + length


def max_decimals(values):
    """
    Return the largest number of characters after the first "." in strings
    in `values`, or 0 if no string contains a ".".

    Equivalent to
    `max((len(v) - v.find(".") for v in values if "." in v), default=1) - 1`.
    """
    cdef:
        np.ndarray[object, ndim=1] arr = np.asarray(values, dtype=object)
        Py_ssize_t i, n = arr.shape[0], length, pos, best = 1
        object value

    for i in range(n):
        value = arr[i]
        if not PyUnicode_Check(value):
            raise TypeError(f"expected str, got {type(value).__name__}")
        length = PyUnicode_GET_LENGTH(value)
        pos = PyUnicode_FindChar(value, ".", 0, length, 1)
        if pos >= 0 and length - pos > best:
            best = length - pos
    return best - 1


cdef extern from "Python.h":
    bint Py_UNICODE_ISSPACE(Py_UCS4 ch)
    Py_UCS4 PyUnicode_READ_CHAR(object s, Py_ssize_t index)


def strip_rows(data, Py_ssize_t rowlen):
    """
    Return rows of `data` with stripped values, skipping rows without
    non-empty values. If `rowlen` > 0, rows are truncated or padded with ""
    to this length.

    Equivalent to `[equal_len([s.strip() for s in row]) for row in data
    if any(row)]`, as in DataTableMixin.adjust_data_width.

    Returns:
        (rows, truncated): `truncated` tells whether any row was truncated.
    """
    cdef:
        list rows = []
        list stripped
        Py_ssize_t i, n, length
        bint truncated = False
        object value

    for row in data:
        if not any(row):
            continue
        stripped = []
        for value in row:
            if PyUnicode_Check(value):
                length = PyUnicode_GET_LENGTH(value)
                if length and (
                        Py_UNICODE_ISSPACE(PyUnicode_READ_CHAR(value, 0))
                        or Py_UNICODE_ISSPACE(
                            PyUnicode_READ_CHAR(value, length - 1))):
                    value = value.strip()
            else:
                value = value.strip()
            stripped.append(value)
        n = len(stripped)
        if n > rowlen > 0:
            del stripped[rowlen:]
            truncated = True
        elif n < rowlen:
            stripped.extend([""] * (rowlen - n))
        rows.append(stripped)
    return rows, truncated


cdef extern from "Python.h":
    char *PyOS_double_to_string(double val, char format_code, int precision,
                                int flags, int *ptype) except NULL
    void PyMem_Free(void *p)


cdef inline str _double_to_str(double value, char code, int precision):
    cdef char *buf = PyOS_double_to_string(value, code, precision, 0, NULL)
    try:
        return buf.decode("ascii")
    finally:
        PyMem_Free(buf)


def format_floats(const double[:] column, const unsigned char[:] wide,
                  str code, int precision, int wide_precision):
    """
    Format values as `f"%.{precision}{code}" % value`, with "" for nan and
    "?" for infinite values. Where `wide` (if given) is nonzero, use
    `wide_precision` and format code "f" instead.

    If the result does not convert back to the same number, the shortest
    string that does is used instead, so no precision is lost. Code "r"
    gives the shortest such string directly.
    """
    cdef:
        Py_ssize_t i, n = column.shape[0]
        list formatted = [None] * n
        double value
        char ccode = ord(code)
        bint has_wide = wide is not None

    for i in range(n):
        value = column[i]
        if value != value:
            formatted[i] = ""
        elif value == INFINITY or value == -INFINITY:
            formatted[i] = "?"
        elif has_wide and wide[i]:
            formatted[i] = _exact_str(value, b'f', wide_precision)
        elif ccode == b'r':
            formatted[i] = _double_to_str(value, b'r', 0)
        else:
            formatted[i] = _exact_str(value, ccode, precision)
    return formatted


cdef str _exact_str(double value, char code, int precision):
    cdef:
        char *buf = PyOS_double_to_string(value, code, precision, 0, NULL)
        char *end
        double parsed
    try:
        parsed = PyOS_string_to_double(buf, &end, NULL)
        if PyErr_Occurred() == NULL and parsed == value:
            return buf.decode("ascii")
        PyErr_Clear()
    finally:
        PyMem_Free(buf)
    return _double_to_str(value, b'r', 0)


def merge_counts(list buckets):
    """
    Merge sorted float arrays without nans.

    Returns sorted unique values across all arrays and a 2-d array with the
    number of occurrences of each value (columns) in each array (rows).
    The cost is linear in the total length times the number of arrays.
    """
    cdef:
        Py_ssize_t k = len(buckets), b, j, n_unique, pass_
        np.ndarray[np.float64_t, ndim=1] data = np.concatenate(
            [np.asarray(x, dtype=np.float64) for x in buckets]
            or [np.empty(0)])
        np.ndarray[np.intp_t, ndim=1] ends = np.cumsum(
            [len(x) for x in buckets], dtype=np.intp)
        np.ndarray[np.intp_t, ndim=1] pos = np.empty(k, dtype=np.intp)
        np.ndarray[np.float64_t, ndim=1] values = np.empty(0)
        np.ndarray[np.float64_t, ndim=2] counts = np.zeros((k, 0))
        double best, v
        bint found

    n_unique = 0
    for pass_ in range(2):
        if pass_ == 1:
            values = np.empty(n_unique)
            counts = np.zeros((k, n_unique))
        for b in range(k):
            pos[b] = 0 if b == 0 else ends[b - 1]
        j = 0
        while True:
            found = False
            for b in range(k):
                if pos[b] < ends[b]:
                    v = data[pos[b]]
                    if not found or v < best:
                        best = v
                        found = True
            if not found:
                break
            for b in range(k):
                while pos[b] < ends[b] and data[pos[b]] == best:
                    if pass_ == 1:
                        counts[b, j] += 1
                    pos[b] += 1
            if pass_ == 1:
                values[j] = best
            j += 1
        n_unique = j
    return values, counts
