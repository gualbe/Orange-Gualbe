"""
Adapt parameters of wrapped scikit-learn estimators to the installed version.

Deprecations are detected from estimators' signatures rather than from version
numbers: scikit-learn marks a deprecated parameter by the default value
"deprecated".
"""
import inspect
from functools import lru_cache

import numpy as np


@lru_cache(maxsize=None)
def deprecated_params(estimator) -> frozenset:
    """Names of `estimator`'s parameters that scikit-learn marks deprecated"""
    return frozenset(
        name
        for name, param in inspect.signature(estimator.__init__).parameters.items()
        if isinstance(param.default, str) and param.default == "deprecated")


@lru_cache(maxsize=None)
def param_default(estimator, name):
    """Default value of `estimator`'s parameter, or None if it does not exist"""
    param = inspect.signature(estimator.__init__).parameters.get(name)
    return None if param is None else param.default


def logistic_regression_params(estimator, params):
    """
    Replace `penalty` (deprecated in scikit-learn 1.8, removed in 1.10) with
    the equivalent `l1_ratio` or `C`, and drop `n_jobs`, which has no effect
    since 1.8.
    """
    if "penalty" not in deprecated_params(estimator):
        return params
    params = dict(params)
    penalty = params.get("penalty")
    if penalty not in ("l1", "l2", None):
        return params  # e.g. elasticnet, which needs an explicit l1_ratio
    del params["penalty"]
    params.pop("n_jobs", None)
    if penalty == "l1":
        params["l1_ratio"] = 1.0
    elif penalty == "l2":
        params["l1_ratio"] = 0.0
    else:
        params["C"] = np.inf
    return params


def mds_params(estimator, params):
    """
    Use `metric_mds` (bool) and `metric` (distance name) in place of `metric`
    (bool) and `dissimilarity`, as introduced in scikit-learn 1.8, and keep
    random initialization, whose default changes in 1.10.
    """
    if param_default(estimator, "metric_mds") is None:
        return params
    params = dict(params)
    params["metric_mds"] = bool(params.pop("metric", True))
    params["metric"] = params.pop("dissimilarity", "euclidean")
    if param_default(estimator, "init") == "warn":
        params["init"] = "random"
    return params


def elastic_net_cv_params(estimator, params):
    """
    Pass the number of alphas as `alphas` (scikit-learn >= 1.7) or as
    `n_alphas` (earlier versions, where `alphas` must be a list or None),
    and drop the deprecated `n_alphas` in 1.7 and 1.8.
    """
    n_alphas_default = param_default(estimator, "n_alphas")
    if n_alphas_default is None:
        return params
    params = dict(params)
    if n_alphas_default == "deprecated":
        params.pop("n_alphas", None)
    elif isinstance(params.get("alphas"), (int, np.integer)):
        params["n_alphas"] = params["alphas"]
        params["alphas"] = None
    return params
