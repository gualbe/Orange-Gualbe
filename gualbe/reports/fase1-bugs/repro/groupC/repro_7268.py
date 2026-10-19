import unittest, traceback, itertools, numpy as np
from Orange.data import Table, Domain, ContinuousVariable, DiscreteVariable, StringVariable
from Orange.widgets.tests.base import WidgetTest
from Orange.widgets.visualize.owboxplot import OWBoxPlot

def kaggle_like_titanic(n=891, seed=0):
    rng = np.random.default_rng(seed)
    surv = DiscreteVariable("Survived", values=("0", "1"))
    pcl = DiscreteVariable("Pclass", values=("1", "2", "3"))
    sex = DiscreteVariable("Sex", values=("female", "male"))
    emb = DiscreteVariable("Embarked", values=("C", "Q", "S"))
    cabin = DiscreteVariable("Cabin", values=tuple(f"C{i}" for i in range(147)))
    age, fare, sib = ContinuousVariable("Age"), ContinuousVariable("Fare"), ContinuousVariable("SibSp")
    X = np.c_[rng.integers(0, 3, n), rng.integers(0, 2, n), rng.integers(0, 3, n).astype(float),
              np.where(rng.random(n) < .77, np.nan, rng.integers(0, 147, n)),
              np.where(rng.random(n) < .2, np.nan, rng.uniform(0, 80, n)), rng.exponential(30, n), rng.integers(0, 5, n)]
    X[rng.random(n) < .005, 2] = np.nan
    return Table.from_numpy(Domain([pcl, sex, emb, cabin, age, fare, sib], surv), X, rng.integers(0, 2, n).astype(float))

class T(WidgetTest):
    def test_all_combos(self):
        for name, data in [("titanic", Table("titanic")), ("housing", Table("housing")),
                           ("heart_disease", Table("heart_disease")), ("kaggle-like titanic", kaggle_like_titanic())]:
            w = self.create_widget(OWBoxPlot)
            self.send_signal(w.Inputs.data, data, widget=w)
            attrs = [a for a in w.attrs]
            groups = [g for g in w.group_vars]
            fails, empty, n = [], [], 0
            for a, g in itertools.product(attrs, groups):
                for opts in [dict(), dict(order_by_importance=True, order_grouping_by_importance=True, compare=1, show_annotations=False, stretched=False, sort_freqs=True)]:
                    for k, v in opts.items(): setattr(w, k, v)
                    try:
                        # emulate GUI: select in list views
                        w.attribute, w.group_var = a, g
                        w._variables_changed(w.apply_group_sorting)
                        w.update_graph()
                        n += 1
                        items = len(w.box_scene.items())
                        if items == 0:
                            empty.append((a.name, g.name if g else None))
                    except Exception as e:
                        fails.append((a.name, g.name if g else None, f"{type(e).__name__}: {e}"))
            print(f"{name}: {n} combos, exceptions={len(fails)}, empty scenes={len(empty)}", fails[:3], empty[:5])

    def test_gui_selection(self):
        w = self.create_widget(OWBoxPlot)
        data = Table("titanic")
        self.send_signal(w.Inputs.data, data, widget=w)
        print("initial: attr", w.attribute, "group", w.group_var, "items", len(w.box_scene.items()))
        # select via the list views (as the user)
        view = w.attr_list; model = view.model()
        for r in range(model.rowCount()):
            view.setCurrentIndex(model.index(r, 0))
            print(" attr->", w.attribute, "items", len(w.box_scene.items()),
                  "display_box visible", w.display_box.isVisibleTo(w), "stretching_box visible", w.stretching_box.isVisibleTo(w))
        gview = w.group_list; gm = gview.model()
        for r in range(gm.rowCount()):
            gview.setCurrentIndex(gm.index(r, 0))
            print(" group->", w.group_var, "items", len(w.box_scene.items()))
unittest.main()
