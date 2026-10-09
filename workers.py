# workers.py

import json
import os
import subprocess
import sys

from PyQt6.QtCore import QRunnable, QThreadPool, QObject, pyqtSignal


class WorkerSignals(QObject):
    """Сигналы для передачи результата из потока в UI."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)


class SaveConfigTask(QRunnable):
    """Сохраняет словарь в JSON-файл в фоновом потоке."""

    def __init__(self, path: str, data: dict):
        super().__init__()
        self.path = path
        self.data = data
        self.signals = WorkerSignals()

    def run(self):
        try:
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
            self.signals.finished.emit(True)
        except Exception as e:
            self.signals.error.emit(str(e))


class OpenPathTask(QRunnable):
    """Открывает файл/папку системным способом в фоне (чтобы UI не подвисал)."""

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        self.signals = WorkerSignals()

    def run(self):
        try:
            if not self.path or not os.path.exists(self.path):
                self.signals.error.emit(f"Путь не существует: {self.path}")
                return
            if sys.platform.startswith("win"):
                os.startfile(self.path)  # noqa
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.path])
            else:
                subprocess.Popen(["xdg-open", self.path])
            self.signals.finished.emit(True)
        except Exception as e:
            self.signals.error.emit(str(e))


class WorkerPool:
    """Обёртка над QThreadPool. Все фоновые задачи идут через него."""

    def __init__(self):
        self._pool = QThreadPool.globalInstance()
        # По умолчанию Qt ставит = кол-во ядер. Ограничим разумным максимумом.
        self._pool.setMaxThreadCount(max(2, min(4, self._pool.maxThreadCount())))

    def save_config(self, path: str, data: dict):
        task = SaveConfigTask(path, data)
        self._pool.start(task)
        return task

    def open_path(self, path: str):
        task = OpenPathTask(path)
        self._pool.start(task)
        return task