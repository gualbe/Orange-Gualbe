import numpy as np
from Orange.data import Table
from Orange.classification import KNNLearner
from Orange.regression import KNNRegressionLearner

iris = Table("iris")
zoo = Table("zoo")
lrn = KNNLearner(metric="mahalanobis")
print("metric_params before:", lrn.params["metric_params"])
m1 = lrn(iris)
print("after fit on iris, V shape:", lrn.params["metric_params"]["V"].shape)

# 1) Same learner, other data with different number of columns -> crash
try:
    m2 = lrn(zoo)
    print("zoo predictions", m2(zoo)[:5])
except Exception as e:
    print("fit on zoo FAILED:", type(e).__name__, str(e)[:200])

# 2) Same number of columns but different data: covariance silently stale
rng = np.random.default_rng(0)
lrn2 = KNNLearner(metric="mahalanobis", n_neighbors=1)
lrn2(iris)  # pollutes V with iris covariance
scaled = iris.copy()
with scaled.unlocked():
    scaled.X = scaled.X * np.array([1000, 1, 1, 0.001])
m_stale = lrn2(scaled)
m_fresh = KNNLearner(metric="mahalanobis", n_neighbors=1)(scaled)
test = scaled[::3]
# use n_neighbors=1 with leave-out? compare neighbours on shifted points
noisy = test.copy()
with noisy.unlocked():
    noisy.X = noisy.X + rng.normal(0, 1, noisy.X.shape) * noisy.X.std(0) * 0.8
ps, pf = m_stale(noisy), m_fresh(noisy)
print("V reused:", np.allclose(lrn2.params["metric_params"]["V"], np.cov(iris.X.T)))
print("predictions differing stale vs fresh:", int((ps != pf).sum()), "of", len(noisy))

# 3) Cross validation: all folds use V from first fold's training data
from Orange.evaluation import CrossValidation, CA
lrn3 = KNNLearner(metric="mahalanobis")
CrossValidation(k=5)(iris, [lrn3])
print("after CV, V == cov(full iris)?", np.allclose(lrn3.params["metric_params"]["V"], np.cov(iris.X.T)))

# 4) Threads: race between two different datasets
import threading
lrn4 = KNNLearner(metric="mahalanobis")
errors = []
def work(d):
    for _ in range(30):
        try:
            lrn4(d)
        except Exception as e:
            errors.append(type(e).__name__)
        lrn4.params["metric_params"] = None
t = [threading.Thread(target=work, args=(d,)) for d in (iris, zoo)]
[x.start() for x in t]; [x.join() for x in t]
print("thread errors:", len(errors), set(errors))
