from PyQt6.QtCore import (
    QObject, 
    QThread, 
    pyqtSignal
)

from PyQt6.QtWidgets import QApplication

from PyQt6.QtCore import Qt

class _Worker(QObject):
    finished = pyqtSignal()
    success = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(self, fn, args, kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.success.emit(result)

        except Exception as e:
            self.error.emit(e)

        finally:
            self.finished.emit()


def run_async(
    *,
    parent_widget,
    fn,
    args=(),
    kwargs=None,
    on_success=None,
    on_error=None,
    on_finished=None,
):
    """
    Runs a function asynchronously while blocking the given widget.

    parent_widget: QWidget to block interaction on
    fn: callable to execute
    args / kwargs: arguments for fn
    on_success(result): called in GUI thread
    on_error(exception): called in GUI thread
    on_finished(): always called in GUI thread
    """

    if kwargs is None:
        kwargs = {}

    # block the parent ui
    parent_widget.setEnabled(False)
    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)

    thread = QThread(parent_widget)
    worker = _Worker(fn, args, kwargs)
    worker.moveToThread(thread)

    # connect
    thread.started.connect(worker.run)

    if on_success:
        worker.success.connect(on_success)

    if on_error:
        worker.error.connect(on_error)

    def _cleanup():
        parent_widget.setEnabled(True)
        QApplication.restoreOverrideCursor()

        if on_finished:
            on_finished()

        worker.deleteLater()
        thread.quit()
        thread.wait()
        thread.deleteLater()

    worker.finished.connect(_cleanup)

    # start
    thread.start()