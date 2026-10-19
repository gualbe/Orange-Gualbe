import gc, sys, time
from concurrent.futures import ThreadPoolExecutor
from AnyQt.QtCore import QObject, Signal, QCoreApplication, Qt

PARENTED = len(sys.argv) > 1 and sys.argv[1] == "parented"

class Progress(QObject):
    advance = Signal()

class Sink(QObject):
    def tick(self): pass

app = QCoreApplication(sys.argv)
sink = Sink()
ex = ThreadPoolExecutor(1)
for i in range(50):
    pr = Progress(sink) if PARENTED else Progress()   # fix in PR #7345: Progress(self)
    pr.advance.connect(sink.tick, Qt.QueuedConnection)
    emit = pr.advance.emit
    f = ex.submit(lambda e=emit: [e() or time.sleep(0.0005) for _ in range(200)])
    time.sleep(0.01)
    pr.advance.disconnect(sink.tick)
    del pr; gc.collect()          # what `self.__awaiting_state = None` does
    app.processEvents()
    f.result()
print("no crash")
