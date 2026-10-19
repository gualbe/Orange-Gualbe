import traceback, numpy as np
from Orange.data import Table
from Orange.classification import KNNLearner
iris, zoo, heart = Table("iris"), Table("zoo"), Table("heart_disease")
for d in (zoo, heart):
    try:
        m = KNNLearner(metric="mahalanobis")(d); m(d[:5]); print(d.name, "fresh OK")
    except Exception as e:
        print(d.name, "fresh FAIL", type(e).__name__, e)
lrn = KNNLearner(metric="mahalanobis"); lrn(iris)
try:
    m = lrn(heart); print("fit ok"); m(heart[:5])
except Exception:
    traceback.print_exc(limit=-3)
# housing: regression
from Orange.regression import KNNRegressionLearner
h = Table("housing")
r = KNNRegressionLearner(metric="mahalanobis"); r(h)
try:
    r(iris.transform(iris.domain)[:, :3] if False else Table("auto-mpg") if False else h[:, 3:])
    print("ok")
except Exception as e: print("regr stale:", type(e).__name__, str(e)[:150])
