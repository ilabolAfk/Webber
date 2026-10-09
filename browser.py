# browser.py

import os
from PyQt6.QtCore import QUrl, QSize, QTimer
from PyQt6.QtGui import QKeySequence, QAction, QShortcut, QIcon
from PyQt6.QtWidgets import (
    QMainWindow, QToolBar, QLineEdit, QTabWidget,
    QStatusBar, QMessageBox, QMenu, QDialog, QApplication
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import (
    QWebEngineSettings, QWebEngineProfile, QWebEnginePage,
    QWebEngineDownloadRequest
)
import qtawesome as qta

from tabbar import BrowserTabBar
from dialogs import FirstRunDialog, APP_NAME
from engines import get_engine
from downloads import DownloadsDialog
from incognito import create_incognito_profile
from themes import THEMES, build_qss


CLR_ICON   = '#e0e0e0'
CLR_ACCENT = '#4285f4'
CLR_MUTED  = '#888888'
CLR_DANGER = '#ea4335'
CLR_INCOG  = '#a142f4'

GITHUB_URL = "https://github.com/ilabolAfk/Webber"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")


def _app_icon(incognito=False):
    """Иконка окна: icon.ico для обычного, FA-маска для инкогнито."""
    if incognito:
        return qta.icon('fa5s.user-secret', color=CLR_INCOG)
    if os.path.exists(ICON_PATH):
        return QIcon(ICON_PATH)
    return qta.icon('fa5s.globe', color=CLR_ACCENT)


# ============================================================
#                       WEB VIEW
# ============================================================

class WebView(QWebEngineView):
    def __init__(self, parent=None, main_window=None, profile=None):
        super().__init__(parent)
        self.main_window = main_window

        if profile is not None:
            page = QWebEnginePage(profile, self)
            self.setPage(page)

        s = self.settings()
        A = QWebEngineSettings.WebAttribute
        s.setAttribute(A.JavascriptEnabled, True)
        s.setAttribute(A.JavascriptCanOpenWindows, True)
        s.setAttribute(A.PluginsEnabled, True)
        s.setAttribute(A.FullScreenSupportEnabled, True)
        s.setAttribute(A.ScrollAnimatorEnabled, True)
        s.setAttribute(A.LocalStorageEnabled, True)

    def createWindow(self, _type):
        if self.main_window:
            return self.main_window.add_new_tab()
        return super().createWindow(_type)


# ============================================================
#                        BROWSER
# ============================================================

class Browser(QMainWindow):
    def __init__(self, engine_config, on_engine_changed=None,
                 on_theme_changed=None, incognito=False, download_dir=None,
                 worker_pool=None):
        super().__init__()
        self.engine_config = engine_config
        self.on_engine_changed = on_engine_changed
        self.on_theme_changed = on_theme_changed
        self.incognito = incognito
        self.worker_pool = worker_pool
        self.download_dir = download_dir or os.path.join(
            os.path.expanduser("~"), "Downloads"
        )
        os.makedirs(self.download_dir, exist_ok=True)

        # ---------- Профиль ----------
        if self.incognito:
            self._incognito = create_incognito_profile()
            self._profile = self._incognito.profile
            self._incognito.set_download_handler(self._on_download_requested)
        else:
            self._incognito = None
            self._profile = QWebEngineProfile.defaultProfile()
            self._profile.downloadRequested.connect(self._on_download_requested)

        # ---------- Заголовок и иконка ----------
        suffix = " — Инкогнито" if self.incognito else ""
        self.setWindowTitle(f"{APP_NAME}{suffix}")
        self.setWindowIcon(_app_icon(self.incognito))
        self.resize(1280, 800)

        # ---------- Вкладки ----------
        self.tabs = QTabWidget()
        self.tabs.setTabBar(BrowserTabBar())
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tabs)

        self._downloads_dialog = None

        self._create_toolbar()
        self.setStatusBar(QStatusBar())
        self._update_status_privacy()
        self._setup_shortcuts()

        if self.incognito:
            QTimer.singleShot(200, self._show_incognito_notice)

        self.add_new_tab(QUrl(self.engine_config["home"]), "Новая вкладка")

    # ============================================================
    #                       TOOLBAR
    # ============================================================
    def _create_toolbar(self):
        tb = QToolBar("Навигация")
        tb.setIconSize(QSize(20, 20))
        tb.setMovable(False)
        self.addToolBar(tb)

        self.btn_back = QAction(qta.icon('fa5s.arrow-left', color=CLR_ICON), "Назад", self)
        self.btn_back.triggered.connect(lambda: self.current_view().back())
        tb.addAction(self.btn_back)

        self.btn_forward = QAction(qta.icon('fa5s.arrow-right', color=CLR_ICON), "Вперёд", self)
        self.btn_forward.triggered.connect(lambda: self.current_view().forward())
        tb.addAction(self.btn_forward)

        self.btn_reload = QAction(qta.icon('fa5s.sync-alt', color=CLR_ICON), "Обновить", self)
        self.btn_reload.triggered.connect(lambda: self.current_view().reload())
        tb.addAction(self.btn_reload)

        self.btn_home = QAction(qta.icon('fa5s.home', color=CLR_ICON), "Домой", self)
        self.btn_home.triggered.connect(self.navigate_home)
        tb.addAction(self.btn_home)

        tb.addSeparator()

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Введите URL или поисковый запрос...")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        tb.addWidget(self.url_bar)

        self.btn_go = QAction(qta.icon('fa5s.location-arrow', color=CLR_ACCENT), "Перейти", self)
        self.btn_go.triggered.connect(self.navigate_to_url)
        tb.addAction(self.btn_go)

        tb.addSeparator()

        self.btn_new_tab = QAction(qta.icon('fa5s.plus', color=CLR_ICON), "Новая вкладка", self)
        self.btn_new_tab.triggered.connect(
            lambda: self.add_new_tab(QUrl(self.engine_config["home"]), "Новая вкладка"))
        tb.addAction(self.btn_new_tab)

        if self.incognito:
            self.btn_incognito = QAction(
                qta.icon('fa5s.user-secret', color=CLR_INCOG),
                "Инкогнито активно", self
            )
            self.btn_incognito.setEnabled(False)
            tb.addAction(self.btn_incognito)
        else:
            self.btn_incognito = QAction(
                qta.icon('fa5s.user-secret', color=CLR_ICON),
                "Новое окно инкогнито (Ctrl+Shift+N)", self
            )
            self.btn_incognito.triggered.connect(self.open_incognito_window)
            tb.addAction(self.btn_incognito)

        self.btn_downloads = QAction(
            qta.icon('fa5s.download', color=CLR_ICON), "Загрузки (Ctrl+J)", self
        )
        self.btn_downloads.triggered.connect(self.show_downloads)
        tb.addAction(self.btn_downloads)

        self.btn_menu = QAction(qta.icon('fa5s.bars', color=CLR_ICON), "Меню", self)
        self.btn_menu.triggered.connect(self.show_menu)
        tb.addAction(self.btn_menu)

    # ============================================================
    #                     SHORTCUTS
    # ============================================================
    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+T"), self,
                  activated=lambda: self.add_new_tab(QUrl(self.engine_config["home"]), "Новая вкладка"))
        QShortcut(QKeySequence("Ctrl+W"), self,
                  activated=lambda: self.close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+L"), self,
                  activated=lambda: (self.url_bar.setFocus(), self.url_bar.selectAll()))
        QShortcut(QKeySequence("F5"), self, activated=lambda: self.current_view().reload())
        QShortcut(QKeySequence("Ctrl+R"), self, activated=lambda: self.current_view().reload())
        QShortcut(QKeySequence("Alt+Left"), self, activated=lambda: self.current_view().back())
        QShortcut(QKeySequence("Alt+Right"), self, activated=lambda: self.current_view().forward())
        QShortcut(QKeySequence("Ctrl+J"), self, activated=self.show_downloads)
        QShortcut(QKeySequence("Ctrl+Shift+N"), self, activated=self.open_incognito_window)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=self.close)

    # ============================================================
    #                        TABS
    # ============================================================
    def add_new_tab(self, url=None, label="Новая вкладка"):
        if isinstance(url, str):
            url = QUrl(url)

        view = WebView(
            main_window=self,
            profile=self._profile if self.incognito else None,
        )
        tab_icon = qta.icon(
            'fa5s.user-secret' if self.incognito else 'fa5s.globe',
            color=CLR_INCOG if self.incognito else CLR_MUTED,
        )

        i = self.tabs.addTab(view, tab_icon, label)
        self.tabs.setCurrentIndex(i)

        view.urlChanged.connect(lambda u, v=view: self.update_urlbar(u, v))
        view.loadFinished.connect(lambda ok, v=view: self.on_load_finished(ok, v))
        view.titleChanged.connect(lambda t, v=view: self.update_tab_title(v, t))
        view.iconChanged.connect(lambda ic, v=view: self.update_tab_icon(v, ic))
        view.page().linkHovered.connect(self.statusBar().showMessage)

        if url and not url.isEmpty():
            view.setUrl(url)
        return view

    def close_tab(self, index):
        if index < 0 or index >= self.tabs.count():
            return
        if self.tabs.count() < 2:
            self.close()
            return
        widget = self.tabs.widget(index)
        self.tabs.removeTab(index)
        if widget:
            widget.deleteLater()

    def current_view(self):
        return self.tabs.currentWidget()

    def on_tab_changed(self, index):
        view = self.tabs.widget(index)
        if view:
            self.url_bar.setText(view.url().toString())
            suffix = " — Инкогнито" if self.incognito else ""
            self.setWindowTitle(f"{view.title()} — {APP_NAME}{suffix}")

    def update_tab_title(self, view, title):
        idx = self.tabs.indexOf(view)
        if idx != -1:
            display = title if title else "Новая вкладка"
            if len(display) > 20:
                display = display[:20] + "..."
            self.tabs.setTabText(idx, display)
        if view is self.current_view():
            suffix = " — Инкогнито" if self.incognito else ""
            self.setWindowTitle(f"{title} — {APP_NAME}{suffix}")

    def update_tab_icon(self, view, icon):
        idx = self.tabs.indexOf(view)
        if idx == -1:
            return
        if self.incognito:
            self.tabs.setTabIcon(idx, qta.icon('fa5s.user-secret', color=CLR_INCOG))
            return
        if not icon.isNull():
            self.tabs.setTabIcon(idx, icon)
        else:
            self.tabs.setTabIcon(idx, qta.icon('fa5s.globe', color=CLR_MUTED))

    def on_load_finished(self, ok, view):
        if not ok:
            self.statusBar().showMessage("Ошибка загрузки страницы", 3000)
        else:
            self._update_status_privacy()

    # ============================================================
    #                PRIVACY / INCOGNITO
    # ============================================================
    def _update_status_privacy(self):
        if self.incognito:
            self.statusBar().setStyleSheet(
                f"QStatusBar {{ background: #2b2b2b; color: {CLR_INCOG}; font-size: 11px; }}"
            )
            self.statusBar().showMessage(
                "Инкогнито: история, cookies и кэш не сохраняются на диск."
            )
            return

        eng = self.engine_config
        if eng["tracking"]:
            self.statusBar().setStyleSheet(
                "QStatusBar { background: #2b2b2b; color: #fbbc05; font-size: 11px; }"
            )
            self.statusBar().showMessage(
                f"Поисковик: {eng['name']}  —  следит за вами. {eng['tracking_note']}"
            )
        else:
            self.statusBar().setStyleSheet(
                "QStatusBar { background: #2b2b2b; color: #34a853; font-size: 11px; }"
            )
            self.statusBar().showMessage(
                f"Поисковик: {eng['name']}  —  не следит за вами. {eng['tracking_note']}"
            )

    def _show_incognito_notice(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Режим инкогнито")
        msg.setIconPixmap(qta.icon('fa5s.user-secret', color=CLR_INCOG).pixmap(48, 48))
        msg.setText("<b>Вы в режиме инкогнито</b>")
        msg.setInformativeText(
            f"{APP_NAME} не сохраняет историю, cookies и данные форм.\n"
            "Файлы, которые вы скачаете, и закладки останутся на диске."
        )
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def open_incognito_window(self):
        win = Browser(
            self.engine_config,
            on_engine_changed=self.on_engine_changed,
            on_theme_changed=self.on_theme_changed,
            incognito=True,
            download_dir=self.download_dir,
            worker_pool=self.worker_pool,
        )
        win.show()
        if not hasattr(self, "_incognito_windows"):
            self._incognito_windows = []
        self._incognito_windows.append(win)

    # ============================================================
    #                     DOWNLOADS
    # ============================================================
    def _on_download_requested(self, item: QWebEngineDownloadRequest):
        fname = item.downloadFileName() or "download"
        item.setDownloadDirectory(self.download_dir)
        item.setDownloadFileName(fname)
        item.accept()

        dlg = self._ensure_downloads_dialog()
        dlg.add_download(item)
        if not dlg.isVisible():
            dlg.show()

    def _ensure_downloads_dialog(self):
        if self._downloads_dialog is None:
            self._downloads_dialog = DownloadsDialog(self, worker_pool=self.worker_pool)
        return self._downloads_dialog

    def show_downloads(self):
        dlg = self._ensure_downloads_dialog()
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    # ============================================================
    #                     NAVIGATION
    # ============================================================
    def navigate_home(self):
        self.current_view().setUrl(QUrl(self.engine_config["home"]))

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        if " " in text or "." not in text:
            query = text.replace(" ", "+")
            url = QUrl(self.engine_config["url"].format(query))
        else:
            if not text.startswith(("http://", "https://", "file://", "about:")):
                text = "https://" + text
            url = QUrl(text)
        self.current_view().setUrl(url)

    def update_urlbar(self, url, view=None):
        if view is not None and view is not self.current_view():
            return
        self.url_bar.setText(url.toString())
        self.url_bar.setCursorPosition(0)

    # ============================================================
    #                        MENU
    # ============================================================
    def show_menu(self):
        menu = QMenu(self)

        menu.addAction(qta.icon('fa5s.plus', color=CLR_ICON),
                       "Новая вкладка  (Ctrl+T)",
                       lambda: self.add_new_tab(QUrl(self.engine_config["home"]), "Новая вкладка"))
        menu.addAction(qta.icon('fa5s.times', color=CLR_ICON),
                       "Закрыть вкладку  (Ctrl+W)",
                       lambda: self.close_tab(self.tabs.currentIndex()))
        menu.addSeparator()
        menu.addAction(qta.icon('fa5s.home', color=CLR_ICON),
                       "Домашняя страница", self.navigate_home)
        menu.addAction(qta.icon('fa5s.sync-alt', color=CLR_ICON),
                       "Обновить  (F5)", lambda: self.current_view().reload())

        menu.addSeparator()

        menu.addAction(qta.icon('fa5s.download', color=CLR_ICON),
                       "Загрузки  (Ctrl+J)", self.show_downloads)

        theme_menu = menu.addMenu(qta.icon('fa5s.palette', color=CLR_ICON), "Тема")
        current_theme = QApplication.instance().property("theme") or "dark"
        for tid, tdata in THEMES.items():
            act = theme_menu.addAction(
                qta.icon(tdata["icon"], color=tdata["icon_color"]),
                tdata["name"],
            )
            act.setCheckable(True)
            act.setChecked(tid == current_theme)
            act.triggered.connect(lambda _, t=tid: self._apply_theme(t))

        if not self.incognito:
            menu.addAction(qta.icon('fa5s.user-secret', color=CLR_INCOG),
                           "Новое окно инкогнито  (Ctrl+Shift+N)",
                           self.open_incognito_window)

        menu.addSeparator()
        menu.addAction(qta.icon('fa5s.search', color=CLR_ICON),
                       "Сменить поисковую систему...", self.change_search_engine)
        menu.addAction(qta.icon('fa5s.code', color=CLR_ICON),
                       "Инструменты разработчика", self.open_devtools)
        menu.addAction(qta.icon('fa5b.github', color=CLR_ICON),
                       "Исходный код на GitHub", self.open_github)
        menu.addAction(qta.icon('fa5s.info-circle', color=CLR_ICON),
                       f"О {APP_NAME}", self.show_about)
        menu.addSeparator()
        menu.addAction(qta.icon('fa5s.sign-out-alt', color=CLR_DANGER),
                       "Выход  (Ctrl+Q)", self.close)

        toolbar = self.findChild(QToolBar)
        btn = toolbar.widgetForAction(self.btn_menu)
        if btn:
            menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    # ============================================================
    #                    THEME HANDLING
    # ============================================================
    def _apply_theme(self, theme_name):
        app = QApplication.instance()
        app.setProperty("theme", theme_name)
        app.setStyleSheet(build_qss(theme_name))
        if self.on_theme_changed:
            self.on_theme_changed(theme_name)

    # ============================================================
    #                    MISC ACTIONS
    # ============================================================
    def open_github(self):
        """Открывает репозиторий Webber в новой вкладке."""
        self.add_new_tab(QUrl(GITHUB_URL), "GitHub — Webber")

    def change_search_engine(self):
        dlg = FirstRunDialog(self, preselected_id=self.engine_config["id"])
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.engine_config = get_engine(dlg.selected_id)
            if self.on_engine_changed:
                self.on_engine_changed(self.engine_config["id"])
            self._update_status_privacy()

    def open_devtools(self):
        view = self.current_view()
        dev = self.add_new_tab(QUrl("about:blank"), "DevTools")
        view.page().setDevToolsPage(dev.page())

    def show_about(self):
        dlg = QMessageBox(self)
        dlg.setWindowTitle(f"О {APP_NAME}")
        dlg.setWindowIcon(_app_icon(False))
        dlg.setIconPixmap(
            qta.icon('fa5s.globe', color=CLR_ACCENT).pixmap(48, 48)
        )

        dlg.setText(
            f"<h3 style='margin:0 0 8px 0;'>{APP_NAME}</h3>"
            "<p style='margin:4px 0;'>"
            "Быстрый и удобный браузер на <b>PyQt6</b> + "
            "<b>QtWebEngine</b> (Chromium 118+).</p>"
            "<p style='margin:4px 0;'>"
            "Иконки — <b>Font Awesome 5</b> через <code>qtawesome</code>.</p>"
            "<p style='margin:4px 0;'>"
            "Темы, менеджер загрузок, режим инкогнито и фоновые задачи — "
            "всё встроено.</p>"
            "<p style='margin:8px 0 0 0;'>"
            "<b>GitHub:</b> "
            f"<a href='{GITHUB_URL}'>{GITHUB_URL}</a></p>"
        )

        btn_open = dlg.addButton(
            "  Открыть на GitHub",
            QMessageBox.ButtonRole.AcceptRole,
        )
        btn_open.setIcon(qta.icon('fa5b.github', color='#ffffff'))
        dlg.addButton("Закрыть", QMessageBox.ButtonRole.RejectRole)

        dlg.exec()

        if dlg.clickedButton() is btn_open:
            self.add_new_tab(QUrl(GITHUB_URL), "GitHub — Webber")