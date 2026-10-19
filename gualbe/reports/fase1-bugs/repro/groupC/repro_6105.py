"""Add the same 2000-point scatter plot to the report N times and count how
many <img> end up in the rendered report page (QtWebEngine)."""
import sys, time, numpy as np
from AnyQt.QtCore import Qt, QCoreApplication
QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
from AnyQt.QtWidgets import QApplication
app = QApplication(sys.argv)
from orangewidget.utils.webview import wait
from orangewidget.report.owreport import OWReport
from Orange.data import Table, Domain, ContinuousVariable, DiscreteVariable
from Orange.widgets.visualize.owscatterplot import OWScatterPlot

rng = np.random.default_rng(0); n = 2000
d = Table.from_numpy(Domain([ContinuousVariable("x"), ContinuousVariable("y")],
                            DiscreteVariable("c", values=("a", "b", "c"))),
                     rng.normal(size=(n, 2)), rng.integers(0, 3, n).astype(float))
w = OWScatterPlot(); w.resize(1000, 700); w.show()
w.set_data(d); w.handleNewSignals()
rep = OWReport(); rep.show()
for i in range(14):
    w.graph.controls.point_width.setValue(i % 5 + 5) if hasattr(w.graph.controls, "point_width") else None
    w.create_report_html(); rep.make_report(w)
    t0 = time.time()
    while time.time() - t0 < 1.5:
        app.processEvents(); time.sleep(0.02)
    total = sum(len(rep.table_model.item(k).html) for k in range(rep.table_model.rowCount()))
    html = rep.report_view.html()
    print(f"items={rep.table_model.rowCount():2d} built_html={total/1e6:5.2f} MB  rendered <img>={html.count('<img')}", flush=True)
