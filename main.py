# main.py

import sys
import json
import os

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QDialog

from engines import SEARCH_ENGINES, DEFAULT_ENGINE_ID, get_engine
from dialogs import FirstRunDialog, APP_NAME
from browser import Browser
from themes import build_qss, DEFAULT_THEME
from workers import WorkerPool


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".webber_config.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # ---------- Иконка приложения (для таскбара, окон, диалогов) ----------
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    pool = WorkerPool()
    cfg = load_config()

    theme = cfg.get("theme", DEFAULT_THEME)
    app.setProperty("theme", theme)
    app.setStyleSheet(build_qss(theme))

    engine_id = cfg.get("search_engine")
    if not engine_id or engine_id not in [e["id"] for e in SEARCH_ENGINES]:
        dlg = FirstRunDialog()
        if dlg.exec() == QDialog.DialogCode.Accepted:
            engine_id = dlg.selected_id or DEFAULT_ENGINE_ID
        else:
            engine_id = DEFAULT_ENGINE_ID
        cfg["search_engine"] = engine_id
        pool.save_config(CONFIG_PATH, cfg)

    def on_engine_changed(new_id):
        cfg["search_engine"] = new_id
        pool.save_config(CONFIG_PATH, cfg)

    def on_theme_changed(new_theme):
        cfg["theme"] = new_theme
        pool.save_config(CONFIG_PATH, cfg)

    engine_config = get_engine(engine_id)
    download_dir = cfg.get("download_dir") or os.path.join(
        os.path.expanduser("~"), "Downloads"
    )

    browser = Browser(
        engine_config,
        on_engine_changed=on_engine_changed,
        on_theme_changed=on_theme_changed,
        download_dir=download_dir,
        worker_pool=pool,
    )
    browser.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()