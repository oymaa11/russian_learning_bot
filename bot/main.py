import asyncio
import os
import random
import tempfile

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from gtts import gTTS

from bot.config import BOT_TOKEN
from bot.db import (
    init_db,
    import_words_from_csv,
    ensure_user,
    get_ui_lang,
    set_ui_lang,
    get_trans_lang,
    set_trans_lang,
    get_category,
    set_category,
    get_next_word_for_user,
    find_word,
    get_quiz_options,
)
from bot.keyboards import (
    main_menu,
    settings_menu,
    ui_language_menu,
    translation_language_menu,
    category_menu,
    audio_button,
    quiz_keyboard,
)


bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

QUIZ_STATE = {}


TEXTS = {
    "ru": {
        "start": "Выберите действие:",
        "settings": "Настройки:",
        "choose_ui": "Выберите язык интерфейса:",
        "choose_trans": "Выберите язык перевода:",
        "choose_category": "Выберите категорию слов:",
        "saved": "✅ Сохранено.",
        "not_found": "Слово не найдено в базе.",
        "no_words": "Слова в выбранной категории не найдены.",
        "word": "Слово",
        "translation": "Перевод",
        "example": "Пример",
        "quiz_start": "Выберите правильный перевод:",
        "quiz_correct": "✅ Правильно!",
        "quiz_wrong": "❌ Неправильно.",
        "correct_answer": "Правильный ответ",
        "need_more_words": "Для теста нужно минимум 4 слова в выбранной категории.",
        "about": (
            "Данный Telegram-бот разработан для эффективного изучения русской лексики "
            "и расширения словарного запаса пользователей.\n\n"
            "Бот предоставляет интерактивный формат обучения, позволяя:\n"
            "• изучать новые слова по тематическим категориям;\n"
            "• получать перевод слов на выбранный язык;\n"
            "• прослушивать аудио слова;\n"
            "• проверять уровень знаний с помощью тестирования;\n"
            "• выполнять быстрый поиск слов через ввод текста.\n\n"
            "Использование бота:\n"
            "1. Перейдите в раздел «Настройки».\n"
            "2. Выберите язык интерфейса и язык перевода.\n"
            "3. Выберите интересующую категорию слов.\n"
            "4. Начните обучение, нажав «Учить слова».\n"
            "5. Для самопроверки используйте раздел «Тест».\n"
            "6. Для поиска слова просто введите его в чат.\n\n"
            "Бот ориентирован на студентов и пользователей, изучающих русский язык, "
            "и может использоваться как вспомогательный инструмент в образовательном процессе."
        ),
        "help": (
            "Как пользоваться ботом:\n\n"
            "1. Откройте «Настройки».\n"
            "2. Выберите язык интерфейса.\n"
            "3. Выберите язык перевода.\n"
            "4. Выберите категорию слов.\n"
            "5. Нажмите «Учить слова» или «Тест».\n"
            "6. Если хотите найти конкретное слово, просто напишите его в чат."
        ),
    },
    "mn": {
        "start": "Үйлдлээ сонгоно уу:",
        "settings": "Тохиргоо:",
        "choose_ui": "Интерфейсийн хэлээ сонгоно уу:",
        "choose_trans": "Орчуулгын хэлээ сонгоно уу:",
        "choose_category": "Үгийн ангиллаа сонгоно уу:",
        "saved": "✅ Хадгалагдлаа.",
        "not_found": "Энэ үг мэдээллийн санд олдсонгүй.",
        "no_words": "Сонгосон ангилалд үг олдсонгүй.",
        "word": "Үг",
        "translation": "Орчуулга",
        "example": "Жишээ",
        "quiz_start": "Зөв орчуулгыг сонгоно уу:",
        "quiz_correct": "✅ Зөв!",
        "quiz_wrong": "❌ Буруу.",
        "correct_answer": "Зөв хариулт",
        "need_more_words": "Тест хийхэд сонгосон ангилалд дор хаяж 4 үг хэрэгтэй.",
        "about": (
            "Энэхүү Telegram чатбот нь орос хэлний үгийн санг үр дүнтэйгээр "
            "сурч эзэмших, хэрэглэгчийн үгийн нөөцийг нэмэгдүүлэх зорилготой.\n\n"
            "Бот нь интерактив сургалтын хэлбэрийг санал болгож, дараах боломжуудыг олгоно:\n"
            "• сэдэвчилсэн ангиллаар шинэ үг сурах;\n"
            "• үгийг сонгосон хэл рүү орчуулах;\n"
            "• үгийн аудио сонсох;\n"
            "• тест ашиглан мэдлэгээ шалгах;\n"
            "• үгийг чат руу шууд бичиж хайх.\n\n"
            "Ашиглах заавар:\n"
            "1. «Тохиргоо» хэсэг рүү орно.\n"
            "2. Интерфейс болон орчуулгын хэлээ сонгоно.\n"
            "3. Сонирхсон үгийн ангиллаа сонгоно.\n"
            "4. «Үг сурах» товчийг дарж сургалтыг эхлүүлнэ.\n"
            "5. «Тест» хэсгийг ашиглан өөрийгөө шалгана.\n"
            "6. Тодорхой үг хайх бол шууд чат руу бичнэ.\n\n"
            "Энэхүү бот нь орос хэл сурч буй оюутан болон хэрэглэгчдэд зориулагдсан "
            "ба сургалтын нэмэлт хэрэгсэл болгон ашиглах боломжтой."
        ),
        "help": (
            "Хэрхэн ашиглах вэ:\n\n"
            "1. «Тохиргоо» хэсэг рүү орно.\n"
            "2. Интерфейсийн хэлээ сонгоно.\n"
            "3. Орчуулгын хэлээ сонгоно.\n"
            "4. Үгийн ангиллаа сонгоно.\n"
            "5. «Үг сурах» эсвэл «Тест» товчийг дарна.\n"
            "6. Тодорхой үг хайх бол үгээ шууд чат руу бичнэ."
        ),
    },
    "en": {
        "start": "Choose an action:",
        "settings": "Settings:",
        "choose_ui": "Choose interface language:",
        "choose_trans": "Choose translation language:",
        "choose_category": "Choose word category:",
        "saved": "✅ Saved.",
        "not_found": "Word not found in the database.",
        "no_words": "No words found in the selected category.",
        "word": "Word",
        "translation": "Translation",
        "example": "Example",
        "quiz_start": "Choose the correct translation:",
        "quiz_correct": "✅ Correct!",
        "quiz_wrong": "❌ Wrong.",
        "correct_answer": "Correct answer",
        "need_more_words": "At least 4 words are required in the selected category.",
        "about": (
            "This Telegram bot is designed to support effective learning of Russian vocabulary "
            "and to help users expand their lexical knowledge.\n\n"
            "The bot provides an interactive learning experience, allowing users to:\n"
            "• learn new words by thematic categories;\n"
            "• receive translations into a selected language;\n"
            "• listen to word audio;\n"
            "• test their knowledge through quizzes;\n"
            "• search for words directly via text input.\n\n"
            "How to use the bot:\n"
            "1. Open the Settings section.\n"
            "2. Choose the interface and translation languages.\n"
            "3. Select a word category.\n"
            "4. Start learning by pressing “Learn words”.\n"
            "5. Use the “Test” section to check your knowledge.\n"
            "6. To find a specific word, simply type it in the chat.\n\n"
            "The bot is intended for students and users learning Russian and can be used "
            "as an auxiliary educational tool."
        ),
        "help": (
            "How to use the bot:\n\n"
            "1. Open Settings.\n"
            "2. Choose the interface language.\n"
            "3. Choose the translation language.\n"
            "4. Choose a word category.\n"
            "5. Press Learn words or Test.\n"
            "6. To find a specific word, just type it in the chat."
        ),
    },
}


START_INFO = (
    "🇷🇺 Добро пожаловать!\n"
    "Если вы хотите изменить язык интерфейса или язык перевода, перейдите в раздел «Настройки».\n\n"
    "🇲🇳 Тавтай морилно уу!\n"
    "Хэрэв интерфейсийн хэл эсвэл орчуулгын хэлийг өөрчлөхийг хүсвэл «Тохиргоо» хэсэг рүү орно уу.\n\n"
    "🇬🇧 Welcome!\n"
    "If you want to change the interface language or translation language, go to Settings."
)


async def tr(user_id: int, key: str) -> str:
    lang = await get_ui_lang(user_id)
    return TEXTS.get(lang, TEXTS["ru"]).get(key, key)


def get_translation(trans_lang: str, ru: str, mn: str | None, en: str | None) -> str:
    if trans_lang == "mn":
        return mn or "—"
    if trans_lang == "en":
        return en or "—"
    return ru


async def send_word(message: Message, row):
    user_id = message.from_user.id
    ui_lang = await get_ui_lang(user_id)
    trans_lang = await get_trans_lang(user_id)

    ru = row["ru"]
    mn = row["mn"]
    en = row["en"]
    image_url = row["image_url"]
    example_ru = row["example_ru"]

    translation = get_translation(trans_lang, ru, mn, en)

    text = (
        f"{await tr(user_id, 'word')}: {ru}\n\n"
        f"{await tr(user_id, 'translation')}: {translation}\n\n"
        f"{await tr(user_id, 'example')}: {example_ru or '—'}"
    )

    if image_url:
        await message.answer_photo(
            photo=image_url,
            caption=text,
            reply_markup=audio_button(ui_lang, ru),
        )
    else:
        await message.answer(
            text,
            reply_markup=audio_button(ui_lang, ru),
        )


@dp.message(Command("start"))
async def start_handler(message: Message):
    await ensure_user(message.from_user.id, message.from_user.username)

    # Анх default ru байх ёстой. DB дээр хуучин user mn болсон бол query ашиглаж reset хийж болно:
    # UPDATE users SET ui_lang='ru';
    ui_lang = await get_ui_lang(message.from_user.id)

    await message.answer(START_INFO, reply_markup=main_menu(ui_lang))
    await message.answer(await tr(message.from_user.id, "start"))


@dp.message(F.text.in_(["📚 Учить слова", "📚 Үг сурах", "📚 Learn words"]))
async def learn_handler(message: Message):
    user_id = message.from_user.id
    category = await get_category(user_id)
    row = await get_next_word_for_user(user_id, category)

    if not row:
        await message.answer(await tr(user_id, "no_words"))
        return

    await send_word(message, row)


@dp.message(F.text.in_(["⚙️ Настройки", "⚙️ Тохиргоо", "⚙️ Settings"]))
async def settings_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)

    await message.answer(
        await tr(message.from_user.id, "settings"),
        reply_markup=settings_menu(ui_lang),
    )


@dp.message(F.text.in_(["🌐 Язык интерфейса", "🌐 Интерфейсийн хэл", "🌐 Interface language"]))
async def ui_language_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)

    await message.answer(
        await tr(message.from_user.id, "choose_ui"),
        reply_markup=ui_language_menu(ui_lang),
    )


@dp.message(F.text.in_(["🔤 Язык перевода", "🔤 Орчуулгын хэл", "🔤 Translation language"]))
async def translation_language_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)

    await message.answer(
        await tr(message.from_user.id, "choose_trans"),
        reply_markup=translation_language_menu(ui_lang),
    )


@dp.message(F.text.in_(["📂 Категория слов", "📂 Үгийн ангилал", "📂 Word category"]))
async def category_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)

    await message.answer(
        await tr(message.from_user.id, "choose_category"),
        reply_markup=category_menu(ui_lang),
    )


@dp.message(F.text.in_(["🇷🇺 Интерфейс: Русский", "🇲🇳 Интерфейс: Монгол", "🇬🇧 Interface: English"]))
async def set_ui_language_handler(message: Message):
    mapping = {
        "🇷🇺 Интерфейс: Русский": "ru",
        "🇲🇳 Интерфейс: Монгол": "mn",
        "🇬🇧 Interface: English": "en",
    }

    new_lang = mapping[message.text]
    await set_ui_lang(message.from_user.id, new_lang)

    await message.answer(
        TEXTS[new_lang]["saved"],
        reply_markup=main_menu(new_lang),
    )


@dp.message(F.text.in_(["🇲🇳 Орчуулга: Монгол", "🇬🇧 Translation: English"]))
async def set_translation_language_handler(message: Message):
    mapping = {
        "🇲🇳 Орчуулга: Монгол": "mn",
        "🇬🇧 Translation: English": "en",
    }

    await set_trans_lang(message.from_user.id, mapping[message.text])

    ui_lang = await get_ui_lang(message.from_user.id)

    await message.answer(
        await tr(message.from_user.id, "saved"),
        reply_markup=main_menu(ui_lang),
    )


@dp.message(F.text.in_([
    "📚 Общий", "⚙️ Инженерия", "💰 Экономика",
    "📚 Ерөнхий", "⚙️ Инженер", "💰 Эдийн засаг",
    "📚 General", "⚙️ Engineering", "💰 Economics",
]))
async def set_category_handler(message: Message):
    mapping = {
        "📚 Общий": "general",
        "⚙️ Инженерия": "engineering",
        "💰 Экономика": "economics",
        "📚 Ерөнхий": "general",
        "⚙️ Инженер": "engineering",
        "💰 Эдийн засаг": "economics",
        "📚 General": "general",
        "⚙️ Engineering": "engineering",
        "💰 Economics": "economics",
    }

    await set_category(message.from_user.id, mapping[message.text])

    ui_lang = await get_ui_lang(message.from_user.id)

    await message.answer(
        await tr(message.from_user.id, "saved"),
        reply_markup=main_menu(ui_lang),
    )


@dp.message(F.text.in_(["📖 Как пользоваться ботом", "📖 Хэрхэн ашиглах вэ", "📖 How to use"]))
async def help_handler(message: Message):
    await message.answer(await tr(message.from_user.id, "help"))


@dp.message(F.text.in_(["ℹ️ О боте", "ℹ️ Ботын тухай", "ℹ️ About"]))
async def about_handler(message: Message):
    await message.answer(await tr(message.from_user.id, "about"))


@dp.message(F.text.in_(["⬅️ Назад", "⬅️ Буцах", "⬅️ Back"]))
async def back_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)

    await message.answer(
        await tr(message.from_user.id, "start"),
        reply_markup=main_menu(ui_lang),
    )


@dp.message(F.text.in_(["🧪 Тест", "🧪 Test"]))
async def quiz_handler(message: Message):
    user_id = message.from_user.id
    category = await get_category(user_id)
    trans_lang = await get_trans_lang(user_id)

    rows = await get_quiz_options(category, 4)

    if len(rows) < 4:
        await message.answer(await tr(user_id, "need_more_words"))
        return

    correct = random.choice(rows)
    correct_id = correct["id"]
    ru = correct["ru"]

    options = []
    for row in rows:
        answer = get_translation(trans_lang, row["ru"], row["mn"], row["en"])
        options.append((row["id"], answer))

    random.shuffle(options)

    correct_answer = get_translation(trans_lang, correct["ru"], correct["mn"], correct["en"])

    QUIZ_STATE[user_id] = {
        "correct_id": correct_id,
        "ru": ru,
        "answer": correct_answer,
    }

    text = (
        f"{await tr(user_id, 'word')}: {ru}\n\n"
        f"{await tr(user_id, 'quiz_start')}"
    )

    await message.answer(text, reply_markup=quiz_keyboard(options))


@dp.callback_query(F.data.startswith("quiz:"))
async def quiz_callback(call: CallbackQuery):
    user_id = call.from_user.id

    if user_id not in QUIZ_STATE:
        await call.answer()
        return

    chosen_id = int(call.data.split(":")[1])
    state = QUIZ_STATE[user_id]

    if chosen_id == state["correct_id"]:
        await call.message.answer(await tr(user_id, "quiz_correct"))
    else:
        await call.message.answer(
            f"{await tr(user_id, 'quiz_wrong')}\n"
            f"{await tr(user_id, 'correct_answer')}: {state['ru']} — {state['answer']}"
        )

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    QUIZ_STATE.pop(user_id, None)
    await call.answer()


@dp.callback_query(F.data.startswith("audio:"))
async def audio_callback(call: CallbackQuery):
    word = call.data.split(":", 1)[1]

    try:
        tts = gTTS(text=word, lang="ru")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            path = tmp.name

        tts.save(path)

        await call.message.answer_audio(
            audio=FSInputFile(path),
            title=word,
        )

        try:
            os.remove(path)
        except OSError:
            pass

    except Exception as e:
        await call.message.answer(f"Audio error: {e}")

    await call.answer()


@dp.message()
async def direct_word_lookup_handler(message: Message):
    text = (message.text or "").strip()

    if not text:
        return

    row = await find_word(text)

    if not row:
        await message.answer(await tr(message.from_user.id, "not_found"))
        return

    await send_word(message, row)


async def main():
    await init_db()

    imported = await import_words_from_csv("words.csv")

    if imported:
        print(f"✅ Imported words: {imported}")
    else:
        print("ℹ️ Үг импортлогдоогүй (аль хэдийн байгаа эсвэл файл олдсонгүй).")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())