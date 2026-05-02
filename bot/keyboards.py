from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


TEXT = {
    "ru": {
        "learn": "📚 Учить слова",
        "quiz": "🧪 Тест",
        "settings": "⚙️ Настройки",
        "about": "ℹ️ О боте",
        "ui_lang": "🌐 Язык интерфейса",
        "trans_lang": "🔤 Язык перевода",
        "category": "📂 Категория слов",
        "help": "📖 Как пользоваться ботом",
        "back": "⬅️ Назад",
        "audio": "🔊 Аудио",

        "cat_general": "📚 Общий",
        "cat_engineering": "⚙️ Инженерия",
        "cat_economics": "💰 Экономика",
    },
    "mn": {
        "learn": "📚 Үг сурах",
        "quiz": "🧪 Тест",
        "settings": "⚙️ Тохиргоо",
        "about": "ℹ️ Ботын тухай",
        "ui_lang": "🌐 Интерфейсийн хэл",
        "trans_lang": "🔤 Орчуулгын хэл",
        "category": "📂 Үгийн ангилал",
        "help": "📖 Хэрхэн ашиглах вэ",
        "back": "⬅️ Буцах",
        "audio": "🔊 Аудио",

        "cat_general": "📚 Ерөнхий",
        "cat_engineering": "⚙️ Инженер",
        "cat_economics": "💰 Эдийн засаг",
    },
    "en": {
        "learn": "📚 Learn words",
        "quiz": "🧪 Test",
        "settings": "⚙️ Settings",
        "about": "ℹ️ About",
        "ui_lang": "🌐 Interface language",
        "trans_lang": "🔤 Translation language",
        "category": "📂 Word category",
        "help": "📖 How to use",
        "back": "⬅️ Back",
        "audio": "🔊 Audio",

        "cat_general": "📚 General",
        "cat_engineering": "⚙️ Engineering",
        "cat_economics": "💰 Economics",
    },
}


def t(lang: str, key: str) -> str:
    return TEXT.get(lang, TEXT["ru"]).get(key, key)


def main_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "learn")), KeyboardButton(text=t(lang, "quiz"))],
            [KeyboardButton(text=t(lang, "settings")), KeyboardButton(text=t(lang, "about"))],
        ],
        resize_keyboard=True,
    )


def settings_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "ui_lang"))],
            [KeyboardButton(text=t(lang, "trans_lang"))],
            [KeyboardButton(text=t(lang, "category"))],
            [KeyboardButton(text=t(lang, "help"))],
            [KeyboardButton(text=t(lang, "back"))],
        ],
        resize_keyboard=True,
    )


def ui_language_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇷🇺 Интерфейс: Русский")],
            [KeyboardButton(text="🇲🇳 Интерфейс: Монгол")],
            [KeyboardButton(text="🇬🇧 Interface: English")],
            [KeyboardButton(text=t(lang, "back"))],
        ],
        resize_keyboard=True,
    )


def translation_language_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇲🇳 Орчуулга: Монгол")],
            [KeyboardButton(text="🇬🇧 Translation: English")],
            [KeyboardButton(text=t(lang, "back"))],
        ],
        resize_keyboard=True,
    )


def category_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "cat_general"))],
            [KeyboardButton(text=t(lang, "cat_engineering"))],
            [KeyboardButton(text=t(lang, "cat_economics"))],
            [KeyboardButton(text=t(lang, "back"))],
        ],
        resize_keyboard=True,
    )


def audio_button(lang: str, word: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "audio"), callback_data=f"audio:{word}")]
        ]
    )