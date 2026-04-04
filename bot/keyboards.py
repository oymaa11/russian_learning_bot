from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

_UI = {
    "mn": {
        "new": "📚 Шинэ үг",
        "rev": "🔁 Давтлага",
        "quiz": "🧪 Тест",
        "lb": "🏆 Тэмцээн",
        "prof": "👤 Профайл",
        "set": "⚙️ Тохиргоо",
        "stats": "📈 Статистик",
        "ph": "Цэснээс сонгоорой…",
        "weak": "❗ Алдаатай үгс",
        "search": "🔎 Үг хайх",
        "grammar": "📖 Дүрэм",
    },
    "ru": {
        "new": "📚 Новые слова",
        "rev": "🔁 Повторение",
        "quiz": "🧪 Тест",
        "lb": "🏆 Соревнование",
        "prof": "👤 Профиль",
        "set": "⚙️ Настройки",
        "stats": "📈 Статистика",
        "ph": "Выберите пункт меню…",
        "weak": "❗ Сложные слова",
        "search": "🔎 Поиск слова",
        "grammar": "📖 Грамматика",
    },
    "en": {
        "new": "📚 New words",
        "rev": "🔁 Review",
        "quiz": "🧪 Quiz",
        "lb": "🏆 Competition",
        "prof": "👤 Profile",
        "set": "⚙️ Settings",
        "stats": "📈 Statistics",
        "ph": "Choose from the menu…",
        "weak": "❗ Difficult words",
        "search": "🔎 Search word",
        "grammar": "📖 Grammar",
    },
}


def kb_ui_language() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇲🇳 Монгол", callback_data="ui:mn"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="ui:en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="ui:ru"),
            ]
        ]
    )


def kb_translation_language() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="MN (орчуулга)", callback_data="tr:mn"),
                InlineKeyboardButton(text="EN (translation)", callback_data="tr:en"),
            ]
        ]
    )


def kb_level() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A1", callback_data="lv:A1"),
                InlineKeyboardButton(text="A2", callback_data="lv:A2"),
            ],
            [
                InlineKeyboardButton(text="B1", callback_data="lv:B1"),
                InlineKeyboardButton(text="B2", callback_data="lv:B2"),
            ],
            [
                InlineKeyboardButton(
                    text="🧪 Placement test (Phase 2)",
                    callback_data="lv:test",
                ),
            ],
        ]
    )


def kb_category() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📘 Общая лексика", callback_data="cat:general")],
            [InlineKeyboardButton(text="⚙️ Инженерная лексика", callback_data="cat:engineering")],
            [InlineKeyboardButton(text="📊 Экономическая лексика", callback_data="cat:economics")],
        ]
    )


def kb_reply_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    t = _UI.get(lang, _UI["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t["new"]), KeyboardButton(text=t["rev"])],
            [KeyboardButton(text=t["quiz"]), KeyboardButton(text=t["lb"])],
            [KeyboardButton(text=t["search"]), KeyboardButton(text=t["grammar"])],
            [KeyboardButton(text=t["prof"]), KeyboardButton(text=t["set"])],
            [KeyboardButton(text=t["stats"]), KeyboardButton(text=t["weak"])],

        ],
        resize_keyboard=True,
        input_field_placeholder=t["ph"],
    )


def kb_settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌐 Язык интерфейса", callback_data="set:ui")],
            [InlineKeyboardButton(text="🌍 Язык перевода", callback_data="set:tr")],
            [InlineKeyboardButton(text="📊 Уровень", callback_data="set:level")],
            [InlineKeyboardButton(text="📚 Категория слов", callback_data="set:category")],
        ]
    )


def kb_ui_language_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇲🇳 Монгол", callback_data="sui:mn"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="sui:en"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="sui:ru"),
            ]
        ]
    )


def kb_translation_language_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="MN (орчуулга)", callback_data="str:mn"),
                InlineKeyboardButton(text="EN (translation)", callback_data="str:en"),
            ]
        ]
    )


def kb_level_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="A1", callback_data="slv:A1"),
                InlineKeyboardButton(text="A2", callback_data="slv:A2"),
            ],
            [
                InlineKeyboardButton(text="B1", callback_data="slv:B1"),
                InlineKeyboardButton(text="B2", callback_data="slv:B2"),
            ],
        ]
    )


def kb_category_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📘 Общая лексика", callback_data="scat:general")],
            [InlineKeyboardButton(text="⚙️ Инженерная лексика", callback_data="scat:engineering")],
            [InlineKeyboardButton(text="📊 Экономическая лексика", callback_data="scat:economics")],
        ]
    )