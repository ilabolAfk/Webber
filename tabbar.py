# tabbar.py

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTabBar


class BrowserTabBar(QTabBar):
    """QTabBar с системным крестиком закрытия (Qt сам рисует и ловит клик)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMovable(True)
        self.setExpanding(False)
        self.setDrawBase(False)
        self.setElideMode(Qt.TextElideMode.ElideRight)
        self.setUsesScrollButtons(True)
        # Включаем встроенные кнопки закрытия — Qt сам их обработает
        self.setTabsClosable(True)

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        size.setWidth(max(size.width(), 180))
        size.setHeight(34)
        return size