from Orange.data import Table
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.unsupervised.owdbscan import OWDBSCAN


class TestDBSCANKeepsEps(WidgetTest):
    # gh-6047: eps set by the user was replaced by the default cut point
    # whenever data arrived (e.g. when the workflow was opened)
    def setUp(self):
        self.iris = Table("iris")

    def test_default_eps_follows_data(self):
        w = self.create_widget(OWDBSCAN)
        self.send_signal(w.Inputs.data, self.iris, widget=w)
        self.assertTrue(w.auto_eps)
        self.assertEqual(w.eps, w.k_distances[w.cut_point])

    def test_eps_set_by_user_is_kept(self):
        w = self.create_widget(OWDBSCAN)
        self.send_signal(w.Inputs.data, self.iris, widget=w)
        w.controls.eps.setValue(0.09)
        self.assertFalse(w.auto_eps)
        self.send_signal(w.Inputs.data, self.iris[::2], widget=w)
        self.assertEqual(w.eps, 0.09)

    def test_stored_eps_is_kept(self):
        w = self.create_widget(
            OWDBSCAN, stored_settings={"eps": 0.09, "auto_eps": False})
        self.send_signal(w.Inputs.data, self.iris, widget=w)
        self.assertEqual(w.eps, 0.09)
        self.assertIsNotNone(self.get_output(w.Outputs.annotated_data,
                                             widget=w))
