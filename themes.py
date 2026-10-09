# themes.py

THEMES = {
    "dark": {
        "name": "Тёмная",
        "icon": "fa5s.moon",
        "icon_color": "#a0a0ff",
        "colors": {
            "bg":        "#1e1e1e",
            "bg_alt":    "#2b2b2b",
            "bg_card":   "#232323",
            "bg_input":  "#1a1a1a",
            "fg":        "#e0e0e0",
            "fg_dim":    "#b0b0b0",
            "fg_muted":  "#888888",
            "accent":    "#4285f4",
            "border":    "#3a3a3a",
            "hover":     "#3d3d3d",
        },
    },
    "light": {
        "name": "Светлая",
        "icon": "fa5s.sun",
        "icon_color": "#f5b400",
        "colors": {
            "bg":        "#f5f5f7",
            "bg_alt":    "#e8e8ec",
            "bg_card":   "#ffffff",
            "bg_input":  "#ffffff",
            "fg":        "#1a1a1a",
            "fg_dim":    "#444444",
            "fg_muted":  "#888888",
            "accent":    "#1a73e8",
            "border":    "#d0d0d5",
            "hover":     "#dadade",
        },
    },
    "midnight": {
        "name": "Полночь",
        "icon": "fa5s.star",
        "icon_color": "#7ab8ff",
        "colors": {
            "bg":        "#0d1117",
            "bg_alt":    "#161b22",
            "bg_card":   "#1c2128",
            "bg_input":  "#0d1117",
            "fg":        "#c9d1d9",
            "fg_dim":    "#8b949e",
            "fg_muted":  "#586069",
            "accent":    "#58a6ff",
            "border":    "#30363d",
            "hover":     "#21262d",
        },
    },
}

DEFAULT_THEME = "dark"


def get_theme(name):
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def build_qss(theme_name):
    """
    QSS применяется ТОЛЬКО к элементам браузера.
    WebEngine (страницы сайтов) остаются нативными — без наших стилей.
    """
    c = get_theme(theme_name)["colors"]
    return f"""
        /* ===================== ОКНО ===================== */
        QMainWindow {{
            background: {c['bg']};
        }}
        QMainWindow QLabel {{
            color: {c['fg']};
            background: transparent;
        }}

        /* ===================== TOOLBAR ===================== */
        QToolBar {{
            background: {c['bg_alt']};
            spacing: 4px;
            padding: 4px;
            border: none;
        }}
        QToolBar QToolButton {{
            background: transparent;
            border-radius: 4px;
            padding: 4px;
        }}
        QToolBar QToolButton:hover {{ background: {c['hover']}; }}
        QToolBar QToolButton:pressed {{ background: {c['border']}; }}

        /* Адресная строка */
        QToolBar QLineEdit {{
            background: {c['bg_input']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 14px;
            padding: 6px 12px;
            font-size: 13px;
        }}
        QToolBar QLineEdit:focus {{ border: 1px solid {c['accent']}; }}

        /* ===================== ВКЛАДКИ ===================== */
        /* Системный крестик Qt остаётся на месте, никаких наших правок */
        QTabWidget::pane {{
            border: none;
            background: {c['bg']};
        }}
        QTabWidget > QTabBar {{
            background: {c['bg_alt']};
        }}
        QTabWidget > QTabBar::tab {{
            background: {c['bg_alt']};
            color: {c['fg_dim']};
            padding: 6px 14px;
            margin-right: 2px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            min-width: 120px;
        }}
        QTabWidget > QTabBar::tab:selected {{
            background: {c['bg']};
            color: {c['fg']};
        }}
        QTabWidget > QTabBar::tab:hover {{ background: {c['hover']}; }}

        /* ===================== СТАТУС-БАР ===================== */
        QStatusBar {{
            background: {c['bg_alt']};
            color: {c['fg_dim']};
        }}

        /* ===================== МЕНЮ ===================== */
        QMenu {{
            background: {c['bg_alt']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            padding: 4px;
        }}
        QMenu::item {{ padding: 6px 28px 6px 8px; border-radius: 4px; }}
        QMenu::item:selected {{ background: {c['accent']}; color: #ffffff; }}
        QMenu::separator {{ height: 1px; background: {c['border']}; margin: 4px 6px; }}

        /* ===================== ДИАЛОГИ ===================== */
        QDialog {{
            background: {c['bg']};
        }}
        QDialog QLabel {{
            color: {c['fg']};
            background: transparent;
        }}
        QDialog QPushButton {{
            background: {c['bg_alt']};
            color: {c['fg']};
            border: 1px solid {c['border']};
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 13px;
        }}
        QDialog QPushButton:hover {{ background: {c['hover']}; }}
        QDialog QCheckBox {{
            color: {c['fg_dim']};
            font-size: 11px;
            spacing: 8px;
        }}
        QDialog QCheckBox::indicator {{
            width: 16px; height: 16px;
            border: 1px solid {c['border']};
            border-radius: 3px;
            background: {c['bg_card']};
        }}
        QDialog QCheckBox::indicator:checked {{
            background: {c['accent']};
            border: 1px solid {c['accent']};
        }}

        /* ===================== ПРОГРЕСС ===================== */
        QDialog QProgressBar {{
            background: {c['bg_input']};
            border: 1px solid {c['border']};
            border-radius: 6px;
            text-align: center;
            color: {c['fg']};
            height: 18px;
            font-size: 11px;
        }}
        QDialog QProgressBar::chunk {{
            background: {c['accent']};
            border-radius: 5px;
        }}

        /* ===================== СКРОЛЛ (только в диалогах) ===================== */
        QDialog QScrollArea {{
            border: none;
            background: transparent;
        }}
        QDialog QScrollBar:vertical {{
            background: {c['bg']};
            width: 8px;
            border-radius: 4px;
        }}
        QDialog QScrollBar::handle:vertical {{
            background: {c['border']};
            border-radius: 4px;
            min-height: 30px;
        }}
        QDialog QScrollBar::handle:vertical:hover {{ background: {c['fg_muted']}; }}
        QDialog QScrollBar::add-line:vertical,
        QDialog QScrollBar::sub-line:vertical {{ height: 0; }}
    """