# incognito.py

from PyQt6.QtWebEngineCore import QWebEngineProfile


class IncognitoProfile:
    """Профиль для режима инкогнито (всё в памяти, ничего на диск)."""

    def __init__(self):
        # QWebEngineProfile без имени → off-the-record
        self.profile = QWebEngineProfile()

        self.profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
        )
        self.profile.setHttpCacheType(
            QWebEngineProfile.HttpCacheType.MemoryHttpCache
        )
        self.profile.setPersistentStoragePath("")
        self.profile.setCachePath("")

        self._download_handler = None

    def set_download_handler(self, handler):
        self._download_handler = handler
        self.profile.downloadRequested.connect(self._on_download)

    def _on_download(self, item):
        if self._download_handler:
            self._download_handler(item)
        item.accept()


def create_incognito_profile():
    return IncognitoProfile()