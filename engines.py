# engines.py

SEARCH_ENGINES = [
    {
        "id": "google",
        "name": "Google",
        "url": "https://www.google.com/search?q={}",
        "home": "https://www.google.com",
        "icon": "fa5b.google",
        "icon_color": "#4285f4",
        "desc": "Самый популярный поисковик. Персонализирует результаты.",
        "tracking": True,
        "tracking_note": "Собирает данные для рекламы и аналитики.",
    },
    {
        "id": "duckduckgo",
        "name": "DuckDuckGo",
        "url": "https://duckduckgo.com/?q={}",
        "home": "https://duckduckgo.com",
        "icon": "fa5s.user-secret",
        "icon_color": "#de5833",
        "desc": "Не отслеживает вас и не сохраняет историю поиска.",
        "tracking": False,
        "tracking_note": "Никакой слежки, никаких персональных данных.",
    },
    {
        "id": "bing",
        "name": "Bing",
        "url": "https://www.bing.com/search?q={}",
        "home": "https://www.bing.com",
        "icon": "fa5b.microsoft",
        "icon_color": "#008373",
        "desc": "Поисковик от Microsoft с интеграцией ИИ.",
        "tracking": True,
        "tracking_note": "Использует данные для улучшения сервисов Microsoft.",
    },
    {
        "id": "brave",
        "name": "Brave Search",
        "url": "https://search.brave.com/search?q={}",
        "home": "https://search.brave.com",
        "icon": "fa5s.shield-alt",
        "icon_color": "#fb542b",
        "desc": "Независимый индекс, приватный поиск по умолчанию.",
        "tracking": False,
        "tracking_note": "Собственный индекс, без слежки за пользователем.",
    },
    {
        "id": "yandex",
        "name": "Яндекс",
        "url": "https://yandex.ru/search/?text={}",
        "home": "https://yandex.ru",
        "icon": "fa5s.search",
        "icon_color": "#fc3f1d",
        "desc": "Российский поисковик с хорошим локальным поиском.",
        "tracking": True,
        "tracking_note": "Собирает данные для персонализации выдачи.",
    },
]

DEFAULT_ENGINE_ID = "duckduckgo"


def get_engine(engine_id):
    for e in SEARCH_ENGINES:
        if e["id"] == engine_id:
            return e
    return SEARCH_ENGINES[1]