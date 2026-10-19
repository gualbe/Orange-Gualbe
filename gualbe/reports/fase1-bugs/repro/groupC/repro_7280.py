import unittest, numpy as np
from sklearn.metrics import silhouette_samples
from Orange.data import Table
from Orange.preprocess import Normalize
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.unsupervised.owkmeans import OWKMeans
from Orange.widgets.visualize.owsilhouetteplot import OWSilhouettePlot

class T(WidgetTest):
    def test_compare(self):
        iris = Table("iris")
        for norm in (True, False):
            km = self.create_widget(OWKMeans, stored_settings={"normalize": norm, "k": 3, "auto_commit": True, "optimize_k": False})
            self.send_signal(km.Inputs.data, iris, widget=km)
            self.wait_until_finished(widget=km)
            out = self.get_output(km.Outputs.annotated_data, widget=km)
            s_km = out.get_column("Silhouette")
            sp = self.create_widget(OWSilhouettePlot, stored_settings={"add_scores": True, "auto_commit": True})
            self.send_signal(sp.Inputs.data, out, widget=sp)
            print("   plot default cluster_var:", sp.cluster_var.name)
            sp.cluster_var = out.domain["Cluster"]; sp._invalidate_scores()
            s_sp = sp._silhouette
            raw = km.clusterings[3].silhouette_samples
            labels = out.get_column("Cluster").astype(int)
            X = Normalize()(iris).X if norm else iris.X
            print(f"normalize={norm}: kmeans meta mean={s_km.mean():.4f} range=[{s_km.min():.3f},{s_km.max():.3f}]; "
                  f"plot mean={s_sp.mean():.4f} range=[{s_sp.min():.3f},{s_sp.max():.3f}]")
            print("   kmeans raw silhouette == plot silhouette:", np.allclose(raw, s_sp),
                  "| max|diff| =", np.abs(raw - s_sp).max().round(4))
            print("   meta == arctan(raw)/pi+.5:", np.allclose(s_km, np.arctan(raw)/np.pi + .5))
            print("   plot == sklearn on un-normalized X:", np.allclose(s_sp, silhouette_samples(iris.X, labels)))
            print("   rank corr kmeans-meta vs plot:", np.corrcoef(np.argsort(np.argsort(s_km)), np.argsort(np.argsort(s_sp)))[0,1].round(3))
            print("   n negatives raw:", (raw < 0).sum(), "min meta (should be <0.5 for negative):", s_km.min().round(3))
            # rank agreement
            print("   avg shown in kmeans table (raw):", km.clusterings[3].silhouette.round(4), " plot avg label:", sp.avg_silhouette_label.text())
unittest.main(defaultTest="T.test_compare")
