# dialogs.py

import os

from PyQt6.QtCore import (
    Qt, pyqtSignal, QPropertyAnimation, QEasingCurve,
    QPoint, QTimer, QParallelAnimationGroup, pyqtProperty
)
from PyQt6.QtGui import QCursor, QIcon
from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QCheckBox,
    QFrame, QVBoxLayout, QHBoxLayout, QScrollArea,
    QWidget, QSizePolicy, QGraphicsOpacityEffect
)
import qtawesome as qta

from engines import SEARCH_ENGINES, DEFAULT_ENGINE_ID


CLR_ACCENT = '#4285f4'
APP_NAME = "Webber"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "icon.ico")


def _dialog_icon():
    """icon.ico для диалогов, если файл существует."""
    if os.path.exists(ICON_PATH):
        return QIcon(ICON_PATH)
    return qta.icon('fa5s.globe', color=CLR_ACCENT)


class SearchEngineCard(QFrame):
    """Карточка поисковой системы с анимациями."""

    clicked = pyqtSignal(str)

    def __init__(self, engine, parent=None):
        super().__init__(parent)

        self._hover_progress = 0.0
        self._check_scale = 1.0

        self.engine = engine
        self.selected = False

        self.setObjectName("engineCard")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # Иконка
        self.icon_label = QLabel()
        icon = qta.icon(engine["icon"], color=engine["icon_color"])
        self.icon_label.setPixmap(icon.pixmap(36, 36))
        self.icon_label.setFixedSize(48, 48)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setStyleSheet("background: transparent;")

        # Название + метка
        name_label = QLabel(engine["name"])
        name_label.setStyleSheet(
            "font-size: 15px; font-weight: 600; color: #ffffff; background: transparent;"
        )

        if engine["tracking"]:
            tag_icon_name = 'fa5s.exclamation-triangle'
            tag_color, tag_bg = '#fbbc05', 'rgba(251,188,5,0.15)'
            tag_text = "СЛЕДИТ"
        else:
            tag_icon_name = 'fa5s.user-shield'
            tag_color, tag_bg = '#34a853', 'rgba(52,168,83,0.15)'
            tag_text = "НЕ СЛЕДИТ"

        self.tag_pix = QLabel()
        self.tag_pix.setPixmap(qta.icon(tag_icon_name, color=tag_color).pixmap(12, 12))
        self.tag_pix.setStyleSheet("background: transparent;")

        tag_label = QLabel(tag_text)
        tag_label.setStyleSheet(
            f"color: {tag_color}; background: {tag_bg}; "
            f"padding: 2px 8px; border-radius: 8px; "
            f"font-size: 10px; font-weight: 700; letter-spacing: 0.5px;"
        )

        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        name_row.addWidget(name_label)
        name_row.addWidget(self.tag_pix)
        name_row.addWidget(tag_label)
        name_row.addStretch()

        # Описание
        desc_label = QLabel(engine["desc"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #b0b0b0; font-size: 12px; background: transparent;")

        # Заметка о приватности
        p_icon = QLabel()
        if engine["tracking"]:
            p_icon.setPixmap(qta.icon('fa5s.times-circle', color='#ea4335').pixmap(11, 11))
            p_color = '#ea4335'
        else:
            p_icon.setPixmap(qta.icon('fa5s.check-circle', color='#34a853').pixmap(11, 11))
            p_color = '#34a853'
        p_icon.setStyleSheet("background: transparent;")

        p_label = QLabel(engine["tracking_note"])
        p_label.setWordWrap(True)
        p_label.setStyleSheet(f"color: {p_color}; font-size: 11px; background: transparent;")

        privacy_row = QHBoxLayout()
        privacy_row.setSpacing(6)
        privacy_row.addWidget(p_icon, 0, Qt.AlignmentFlag.AlignTop)
        privacy_row.addWidget(p_label, 1)

        # Галочка
        self.check_icon = QLabel()
        self.check_icon.setFixedSize(28, 28)
        self.check_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.check_icon.setStyleSheet("background: transparent;")
        self.check_icon.setPixmap(qta.icon('fa5s.circle', color='#555555').pixmap(22, 22))

        text_layout = QVBoxLayout()
        text_layout.setSpacing(6)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.addLayout(name_row)
        text_layout.addWidget(desc_label)
        text_layout.addLayout(privacy_row)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)
        main_layout.addWidget(self.icon_label, 0, Qt.AlignmentFlag.AlignTop)
        main_layout.addLayout(text_layout, 1)
        main_layout.addWidget(self.check_icon, 0, Qt.AlignmentFlag.AlignVCenter)

        # Анимации
        self._check_anim = QPropertyAnimation(self, b"checkScale")
        self._check_anim.setDuration(220)
        self._check_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        self._hover_anim = QPropertyAnimation(self, b"hoverProgress")
        self._hover_anim.setDuration(150)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._apply_style()

        if engine["tracking"]:
            self._start_pulse()

    def get_check_scale(self):
        return self._check_scale

    def set_check_scale(self, value):
        self._check_scale = value
        size = max(1, int(22 * value))
        if self.selected:
            icon = qta.icon('fa5s.check-circle', color=CLR_ACCENT)
        else:
            icon = qta.icon('fa5s.circle', color='#555555')
        self.check_icon.setPixmap(icon.pixmap(size, size))

    checkScale = pyqtProperty(float, get_check_scale, set_check_scale)

    def get_hover_progress(self):
        return self._hover_progress

    def set_hover_progress(self, value):
        self._hover_progress = value
        self._apply_style()

    hoverProgress = pyqtProperty(float, get_hover_progress, set_hover_progress)

    def _start_pulse(self):
        self._pulse_state = False

        def toggle():
            self._pulse_state = not self._pulse_state
            color = '#fbbc05' if self._pulse_state else '#7a5a00'
            self.tag_pix.setPixmap(
                qta.icon('fa5s.exclamation-triangle', color=color).pixmap(12, 12)
            )

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(toggle)
        self._pulse_timer.start(700)

    def _apply_style(self):
        if self.selected:
            border = CLR_ACCENT
            bg = "#1a2a44"
        else:
            p = self._hover_progress
            v = int(0x23 + (0x2a - 0x23) * p)
            bg = f"#{v:02x}{v:02x}{v:02x}"
            r = int(0x3a + (0x5a - 0x3a) * p)
            border = f"#{r:02x}{r:02x}{r:02x}"

        self.setStyleSheet(f"""
            QFrame#engineCard {{
                background: {bg};
                border: 2px solid {border};
                border-radius: 10px;
            }}
        """)

    def set_selected(self, value):
        if self.selected == value:
            return
        self.selected = value
        self._apply_style()
        self._check_anim.stop()
        self._check_anim.setStartValue(0.5)
        self._check_anim.setEndValue(1.0)
        self._check_anim.start()

    def enterEvent(self, event):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._hover_progress)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.engine["id"])
        super().mousePressEvent(event)


class FirstRunDialog(QDialog):
    """Экран первого запуска — выбор поисковой системы."""

    def __init__(self, parent=None, preselected_id=None):
        super().__init__(parent)
        self.setWindowTitle(f"Первый запуск — {APP_NAME}")
        self.setWindowIcon(_dialog_icon())
        self.setModal(True)
        self.setMinimumSize(560, 640)
        self.resize(580, 760)

        self.selected_id = None
        self.cards = {}

        self.setStyleSheet("""
            QDialog { background: #1a1a1a; }
            QLabel { background: transparent; }
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #1a1a1a; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical {
                background: #3d3d3d; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background: #555; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(14)

        logo = QLabel()
        if os.path.exists(ICON_PATH):
            pix = QIcon(ICON_PATH).pixmap(52, 52)
            logo.setPixmap(pix)
        else:
            logo.setPixmap(qta.icon('fa5s.globe', color=CLR_ACCENT).pixmap(52, 52))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(f"Добро пожаловать в {APP_NAME}")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: 700;")

        subtitle = QLabel(
            "Выберите поисковую систему по умолчанию.\n"
            "Мы показываем, какие сервисы собирают ваши данные, а какие — нет."
        )
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #a0a0a0; font-size: 12px;")

        root.addWidget(logo)
        root.addWidget(title)
        root.addWidget(subtitle)
        root.addSpacing(4)

        legend = QHBoxLayout()
        legend.setSpacing(8)
        legend.addStretch()

        l1 = QLabel()
        l1.setPixmap(qta.icon('fa5s.exclamation-triangle', color='#fbbc05').pixmap(12, 12))
        l1t = QLabel("Следит за вами")
        l1t.setStyleSheet("color: #fbbc05; font-size: 11px;")

        l2 = QLabel()
        l2.setPixmap(qta.icon('fa5s.user-shield', color='#34a853').pixmap(12, 12))
        l2t = QLabel("Не следит")
        l2t.setStyleSheet("color: #34a853; font-size: 11px;")

        legend.addWidget(l1)
        legend.addWidget(l1t)
        legend.addSpacing(16)
        legend.addWidget(l2)
        legend.addWidget(l2t)
        legend.addStretch()
        root.addLayout(legend)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        cards_container = QWidget()
        cards_container.setStyleSheet("background: transparent;")
        cards_layout = QVBoxLayout(cards_container)
        cards_layout.setContentsMargins(4, 4, 4, 4)
        cards_layout.setSpacing(10)

        self._cards_for_anim = []
        for engine in SEARCH_ENGINES:
            card = SearchEngineCard(engine)
            card.clicked.connect(self.select_engine)
            self.cards[engine["id"]] = card
            cards_layout.addWidget(card)
            self._cards_for_anim.append(card)

        cards_layout.addStretch()
        scroll.setWidget(cards_container)
        root.addWidget(scroll, 1)

        self.chk_agree = QCheckBox(
            "Я понимаю, что выбранная поисковая система может собирать данные обо мне"
        )
        self.chk_agree.setStyleSheet("""
            QCheckBox { color: #b0b0b0; font-size: 11px; spacing: 8px; }
            QCheckBox::indicator {
                width: 16px; height: 16px;
                border: 1px solid #555; border-radius: 3px;
                background: #232323;
            }
            QCheckBox::indicator:checked {
                background: #4285f4; border: 1px solid #4285f4;
            }
        """)
        self.chk_agree.setChecked(True)
        self.chk_agree.stateChanged.connect(self._update_buttons)
        root.addWidget(self.chk_agree)

        footer = QLabel(
            f"{APP_NAME} не передаёт ваши данные третьим лицам. "
            "Слежка зависит только от выбранной вами поисковой системы."
        )
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setWordWrap(True)
        footer.setStyleSheet("color: #666; font-size: 10px; padding: 4px;")
        root.addWidget(footer)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_skip = QPushButton("  Пропустить")
        self.btn_skip.setIcon(qta.icon('fa5s.forward', color='#c0c0c0'))
        self.btn_skip.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_skip.setStyleSheet("""
            QPushButton {
                background: #2b2b2b; color: #c0c0c0;
                border: 1px solid #3d3d3d; border-radius: 8px;
                padding: 10px 16px; font-size: 13px;
            }
            QPushButton:hover { background: #3d3d3d; }
        """)
        self.btn_skip.clicked.connect(self.on_skip)

        self.btn_continue = QPushButton("  Продолжить")
        self.btn_continue.setIcon(qta.icon('fa5s.check', color='#ffffff'))
        self.btn_continue.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_continue.setStyleSheet("""
            QPushButton {
                background: #4285f4; color: #ffffff;
                border: none; border-radius: 8px;
                padding: 10px 20px; font-size: 13px; font-weight: 600;
            }
            QPushButton:hover { background: #5a95f5; }
            QPushButton:disabled { background: #2c3e5c; color: #7a8aa0; }
        """)
        self.btn_continue.clicked.connect(self.on_continue)

        btn_row.addWidget(self.btn_skip)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_continue)
        root.addLayout(btn_row)

        self.select_engine(preselected_id or DEFAULT_ENGINE_ID)
        QTimer.singleShot(0, self._animate_appearance)

    def _animate_appearance(self):
        for i, card in enumerate(self._cards_for_anim):
            eff = QGraphicsOpacityEffect(card)
            eff.setOpacity(0.0)
            card.setGraphicsEffect(eff)

            fade = QPropertyAnimation(eff, b"opacity", self)
            fade.setDuration(260)
            fade.setStartValue(0.0)
            fade.setEndValue(1.0)
            fade.setEasingCurve(QEasingCurve.Type.OutCubic)

            end_pos = card.pos()
            slide = QPropertyAnimation(card, b"pos", self)
            slide.setDuration(320)
            slide.setStartValue(end_pos + QPoint(0, 20))
            slide.setEndValue(end_pos)
            slide.setEasingCurve(QEasingCurve.Type.OutBack)

            group = QParallelAnimationGroup(self)
            group.addAnimation(fade)
            group.addAnimation(slide)

            QTimer.singleShot(i * 60, lambda g=group: g.start())

    def select_engine(self, engine_id):
        self.selected_id = engine_id
        for eid, card in self.cards.items():
            card.set_selected(eid == engine_id)
        self._update_buttons()

    def _update_buttons(self):
        if not hasattr(self, "btn_continue"):
            return
        engine = next((e for e in SEARCH_ENGINES if e["id"] == self.selected_id), None)
        need_agree = bool(engine and engine["tracking"])
        self.btn_continue.setEnabled(
            (not need_agree) or self.chk_agree.isChecked()
        )

    def on_continue(self):
        if self.selected_id:
            self.accept()

    def on_skip(self):
        self.selected_id = DEFAULT_ENGINE_ID
        self.accept()