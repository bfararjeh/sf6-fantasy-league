from PyQt6.QtCore import QThread, QObject, pyqtSignal

class _BuildWorker(QObject):
    finished = pyqtSignal()

    def __init__(self, fn):
        super().__init__()
        self.fn = fn

    def run(self):
        self.fn()
        self.finished.emit()


def load_view(stack, placeholder, build_fn, on_done, thread_registry=None):
    stack.setCurrentWidget(placeholder)
    intended_widget = placeholder  # track what we showed

    thread = QThread()
    worker = _BuildWorker(build_fn)
    worker.moveToThread(thread)

    if thread_registry is not None:
        thread_registry.append(thread)

    thread.started.connect(worker.run)

    def _finish():
        on_done()
        if stack.currentWidget() is placeholder:
            new_widget = stack.widget(stack.count() - 1)
            stack.setCurrentWidget(new_widget)
        worker.deleteLater()
        thread.quit()
        thread.wait()
        thread.deleteLater()
        if thread_registry is not None:
            try:
                thread_registry.remove(thread)
            except ValueError:
                pass

    worker.finished.connect(_finish)
    thread.start()