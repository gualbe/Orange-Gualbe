import numpy as np
from sklearn.metrics import silhouette_samples

from Orange.data import Table
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.unsupervised.owkmeans import OWKMeans


class TestKMeansSilhouetteScore(WidgetTest):
    # gh-7280: "Silhouette" holds arctan-mapped values; "Silhouette score"
    # holds the silhouettes themselves
    def test_silhouette_score(self):
        iris = Table("iris")
        w = self.create_widget(OWKMeans, stored_settings={
            "auto_commit": True, "normalize": False, "k": 3,
            "optimize_k": False})
        self.send_signal(w.Inputs.data, iris, widget=w)
        self.wait_until_finished(w)
        out = self.get_output(w.Outputs.annotated_data, widget=w)
        clusters = out.get_column("Cluster").astype(int)
        expected = silhouette_samples(iris.X, clusters)
        score = out.get_column("Silhouette score")
        np.testing.assert_almost_equal(score, expected)
        np.testing.assert_almost_equal(out.get_column("Silhouette"),
                                       np.arctan(expected) / np.pi + 0.5)

        centroids = self.get_output(w.Outputs.centroids, widget=w)
        for i, mean in enumerate(centroids.get_column("Silhouette score")):
            self.assertAlmostEqual(mean, expected[clusters == i].mean())
