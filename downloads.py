# downloads.py

import os
import subprocess
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QFrame, QProgressBar, QSizePolicy
)
from PyQt6.QtWebEngineCore import QWebEngineDownloadRequest
import qtawesome as qta


CLR_ACCENT = '#4285f4'
CLR_DANGER = '#ea4335'
CLR_OK     = '#34a853'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")


def _dialog_icon():
    if os.path.exists(ICON_PATH):
        return QIcon(ICON_PATH)
    return qta.icon('fa5s.download', color=CLR_ACCENT)


def _open_path_fallback(path):
    """Синхронный fallback, если worker_pool не передан."""
    if not path or not os.path.exists(path):
        return
    if sys.platform.startswith("win"):
        os.startfile(path)  # noqa
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


class DownloadItem(QFrame):
    """Одна строка в списке загрузок."""

    def __init__(self, item: QWebEngineDownloadRequest, parent=None, worker_pool=None):
        super().__init__(parent)
        self.item = item
        self.worker_pool = worker_pool
        self.setObjectName("downloadItem")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        fname = item.downloadFileName()
        self._full_path = os.path.join(item.downloadDirectory(), fname)

        ext = os.path.splitext(fname)[1].lower()
        icon_name, icon_color = self._icon_for_ext(ext)

        self.icon_label = QLabel()
        self.icon_label.setPixmap(qta.icon(icon_name, color=icon_color).pixmap(28, 28))
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")

        self.name_label = QLabel(fname or "загрузка")
        self.name_label.setStyleSheet("font-size: 13px; font-weight: 600;")
        self.name_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.status_label = QLabel("Ожидание...")
        self.status_label.setStyleSheet("font-size: 11px; color: #888888;")

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.btn_pause = QPushButton()
        self.btn_pause.setIcon(qta.icon('fa5s.pause', color='#e0e0e0'))
        self.btn_pause.setToolTip("Пауза")
        self.btn_pause.setFixedSize(30, 30)
        self.btn_pause.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_pause.setStyleSheet(self._btn_qss())
        self.btn_pause.clicked.connect(self.toggle_pause)

        self.btn_cancel = QPushButton()
        self.btn_cancel.setIcon(qta.icon('fa5s.times', color=CLR_DANGER))
        self.btn_cancel.setToolTip("Отменить")
        self.btn_cancel.setFixedSize(30, 30)
        self.btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancel.setStyleSheet(self._btn_qss())
        self.btn_cancel.clicked.connect(self.cancel)

        self.btn_open = QPushButton()
        self.btn_open.setIcon(qta.icon('fa5s.external-link-alt', color='#e0e0e0'))
        self.btn_open.setToolTip("Открыть файл")
        self.btn_open.setFixedSize(30, 30)
        self.btn_open.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open.setStyleSheet(self._btn_qss())
        self.btn_open.setEnabled(False)
        self.btn_open.clicked.connect(self._open_file)

        self.btn_folder = QPushButton()
        self.btn_folder.setIcon(qta.icon('fa5s.folder-open', color='#e0e0e0'))
        self.btn_folder.setToolTip("Показать в папке")
        self.btn_folder.setFixedSize(30, 30)
        self.btn_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_folder.setStyleSheet(self._btn_qss())
        self.btn_folder.clicked.connect(self._open_folder)

        info = QVBoxLayout()
        info.setSpacing(4)
        info.setContentsMargins(0, 0, 0, 0)
        info.addWidget(self.name_label)
        info.addWidget(self.progress)
        info.addWidget(self.status_label)

        btns = QHBoxLayout()
        btns.setSpacing(4)
        btns.addWidget(self.btn_pause)
        btns.addWidget(self.btn_cancel)
        btns.addWidget(self.btn_open)
        btns.addWidget(self.btn_folder)

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 10, 12, 10)
        row.setSpacing(12)
        row.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignTop)
        row.addLayout(info, 1)
        row.addLayout(btns, 0)

        self.setStyleSheet("""
            QFrame#downloadItem {
                background: #232323;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
            }
        """)

        # Сигналы PyQt6
        item.receivedBytesChanged.connect(self.on_received_bytes_changed)
        item.isFinishedChanged.connect(self.on_finished)
        item.stateChanged.connect(self.on_state_changed)

        self.on_state_changed(item.state())

    @staticmethod
    def _btn_qss():
        return """
            QPushButton {
                background: transparent; border: 1px solid #3a3a3a;
                border-radius: 6px; padding: 0;
            }
            QPushButton:hover { background: #3d3d3d; }
            QPushButton:disabled { background: transparent; border-color: #2a2a2a; }
        """

    @staticmethod
    def _icon_for_ext(ext):
        mapping = {
            ".zip":  ("fa5s.file-archive", "#f0ad4e"),
            ".rar":  ("fa5s.file-archive", "#f0ad4e"),
            ".7z":   ("fa5s.file-archive", "#f0ad4e"),
            ".tar":  ("fa5s.file-archive", "#f0ad4e"),
            ".gz":   ("fa5s.file-archive", "#f0ad4e"),
            ".pdf":  ("fa5s.file-pdf",     "#ea4335"),
            ".doc":  ("fa5s.file-word",    "#4285f4"),
            ".docx": ("fa5s.file-word",    "#4285f4"),
            ".xls":  ("fa5s.file-excel",   "#34a853"),
            ".xlsx": ("fa5s.file-excel",   "#34a853"),
            ".ppt":  ("fa5s.file-powerpoint", "#ea4335"),
            ".pptx": ("fa5s.file-powerpoint", "#ea4335"),
            ".jpg":  ("fa5s.file-image",   "#a142f4"),
            ".jpeg": ("fa5s.file-image",   "#a142f4"),
            ".png":  ("fa5s.file-image",   "#a142f4"),
            ".gif":  ("fa5s.file-image",   "#a142f4"),
            ".webp": ("fa5s.file-image",   "#a142f4"),
            ".svg":  ("fa5s.file-image",   "#a142f4"),
            ".mp3":  ("fa5s.file-audio",   "#1db954"),
            ".wav":  ("fa5s.file-audio",   "#1db954"),
            ".flac": ("fa5s.file-audio",   "#1db954"),
            ".mp4":  ("fa5s.file-video",   "#ff0000"),
            ".mkv":  ("fa5s.file-video",   "#ff0000"),
            ".avi":  ("fa5s.file-video",   "#ff0000"),
            ".mov":  ("fa5s.file-video",   "#ff0000"),
            ".exe":  ("fa5s.file-code",    "#888888"),
            ".msi":  ("fa5s.file-code",    "#888888"),
            ".txt":  ("fa5s.file-alt",     "#b0b0b0"),
            ".md":   ("fa5s.file-alt",     "#b0b0b0"),
            ".html": ("fa5s.file-code",    "#e34c26"),
            ".htm":  ("fa5s.file-code",    "#e34c26"),
            ".css":  ("fa5s.file-code",    "#264de4"),
            ".js":   ("fa5s.file-code",    "#f0db4f"),
            ".py":   ("fa5s.file-code",    "#3572a5"),
            ".json": ("fa5s.file-code",    "#888888"),
            ".xml":  ("fa5s.file-code",    "#888888"),
        }
        return mapping.get(ext, ("fa5s.file", "#b0b0b0"))

    def _open_file(self):
        if self.worker_pool:
            self.worker_pool.open_path(self._full_path)
        else:
            _open_path_fallback(self._full_path)

    def _open_folder(self):
        d = self.item.downloadDirectory()
        if self.worker_pool:
            self.worker_pool.open_path(d)
        else:
            _open_path_fallback(d)

    def on_received_bytes_changed(self):
        received = self.item.receivedBytes()
        total = self.item.totalBytes()

        if total > 0:
            pct = int(received * 100 / total)
            self.progress.setRange(0, 100)
            self.progress.setValue(pct)
            self.status_label.setText(
                f"{received / 1024 / 1024:.1f} / {total / 1024 / 1024:.1f} МБ"
            )
        else:
            self.progress.setRange(0, 0)
            self.status_label.setText(f"{received / 1024 / 1024:.1f} МБ")

    def on_state_changed(self, state):
        S = QWebEngineDownloadRequest.DownloadState
        if state == S.DownloadRequested:
            self.status_label.setText("Ожидание...")
        elif state == S.DownloadInProgress:
            self.status_label.setText("Загрузка...")
            self.btn_pause.setIcon(qta.icon('fa5s.pause', color='#e0e0e0'))
            self.btn_pause.setToolTip("Пауза")
        elif state == S.DownloadCompleted:
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            self.status_label.setText("Завершено")
            self.status_label.setStyleSheet("font-size: 11px; color: #34a853;")
            self.btn_pause.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            self.btn_open.setEnabled(True)
        elif state == S.DownloadCancelled:
            self.status_label.setText("Отменено")
            self.status_label.setStyleSheet("font-size: 11px; color: #ea4335;")
            self.btn_pause.setEnabled(False)
            self.btn_cancel.setEnabled(False)
        elif state == S.DownloadInterrupted:
            self.status_label.setText("Прервано")
            self.status_label.setStyleSheet("font-size: 11px; color: #ea4335;")
            self.btn_pause.setEnabled(False)
            self.btn_cancel.setEnabled(False)

    def on_finished(self):
        if self.item.isFinished():
            self.progress.setRange(0, 100)
            self.progress.setValue(100)
            self.status_label.setText("Завершено")
            self.status_label.setStyleSheet("font-size: 11px; color: #34a853;")
            self.btn_pause.setEnabled(False)
            self.btn_cancel.setEnabled(False)
            self.btn_open.setEnabled(True)

    def toggle_pause(self):
        S = QWebEngineDownloadRequest.DownloadState
        if self.item.state() == S.DownloadInProgress:
            self.item.pause()
            self.btn_pause.setIcon(qta.icon('fa5s.play', color='#e0e0e0'))
            self.btn_pause.setToolTip("Продолжить")
            self.status_label.setText("Пауза")
        elif self.item.isPaused():
            self.item.resume()
            self.btn_pause.setIcon(qta.icon('fa5s.pause', color='#e0e0e0'))
            self.btn_pause.setToolTip("Пауза")
            self.status_label.setText("Загрузка...")

    def cancel(self):
        self.item.cancel()


class DownloadsDialog(QDialog):
    """Окно менеджера загрузок."""

    def __init__(self, parent=None, worker_pool=None):
        super().__init__(parent)
        self.worker_pool = worker_pool
        self.setWindowTitle("Загрузки")
        self.setWindowIcon(_dialog_icon())
        self.setMinimumSize(620, 480)
        self.resize(680, 540)

        self.setStyleSheet("""
            QDialog { background: #1e1e1e; }
            QLabel { background: transparent; }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1e1e1e; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical {
                background: #3d3d3d; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #555; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 16)
        root.setSpacing(12)

        head = QHBoxLayout()
        head.setSpacing(8)
        t_icon = QLabel()
        t_icon.setPixmap(qta.icon('fa5s.download', color=CLR_ACCENT).pixmap(20, 20))
        title = QLabel("Загрузки")
        title.setStyleSheet("color: #ffffff; font-size: 16px; font-weight: 700;")
        head.addWidget(t_icon)
        head.addWidget(title)
        head.addStretch()
        root.addLayout(head)

        self.empty = QLabel("Пока нет загрузок.\nСкачанные файлы появятся здесь.")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setStyleSheet("color: #666; font-size: 12px; padding: 40px;")
        root.addWidget(self.empty)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        self.items_layout = QVBoxLayout(container)
        self.items_layout.setContentsMargins(4, 4, 4, 4)
        self.items_layout.setSpacing(8)
        self.items_layout.addStretch()

        self.scroll.setWidget(container)
        self.scroll.setVisible(False)
        root.addWidget(self.scroll, 1)

        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        self.btn_open_folder = QPushButton("  Открыть папку загрузок")
        self.btn_open_folder.setIcon(qta.icon('fa5s.folder-open', color='#e0e0e0'))
        self.btn_open_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background: #2b2b2b; color: #e0e0e0;
                border: 1px solid #3d3d3d; border-radius: 8px;
                padding: 8px 14px; font-size: 12px;
            }
            QPushButton:hover { background: #3d3d3d; }
        """)
        self.btn_open_folder.clicked.connect(self.open_download_folder)

        self.btn_clear = QPushButton("  Очистить список")
        self.btn_clear.setIcon(qta.icon('fa5s.broom', color='#e0e0e0'))
        self.btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_clear.setStyleSheet(self.btn_open_folder.styleSheet())
        self.btn_clear.clicked.connect(self.clear_finished)

        bottom.addWidget(self.btn_open_folder)
        bottom.addStretch()
        bottom.addWidget(self.btn_clear)
        root.addLayout(bottom)

    def add_download(self, item):
        d = DownloadItem(item, worker_pool=self.worker_pool)
        self.items_layout.insertWidget(self.items_layout.count() - 1, d)
        self._refresh_visibility()
        return d

    def _refresh_visibility(self):
        has = self.items_layout.count() > 1
        self.empty.setVisible(not has)
        self.scroll.setVisible(has)

    def clear_finished(self):
        S = QWebEngineDownloadRequest.DownloadState
        for i in reversed(range(self.items_layout.count())):
            w = self.items_layout.itemAt(i).widget()
            if isinstance(w, DownloadItem):
                state = w.item.state()
                if state in (S.DownloadCompleted, S.DownloadCancelled, S.DownloadInterrupted):
                    w.setParent(None)
                    w.deleteLater()
        self._refresh_visibility()

    def open_download_folder(self):
        path = os.path.join(os.path.expanduser("~"), "Downloads")
        if self.worker_pool:
            self.worker_pool.open_path(path)
        else:
            _open_path_fallback(path)