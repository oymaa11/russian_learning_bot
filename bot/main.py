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
    init_db, close_pool, import_words_from_csv,
    ensure_user, get_user_settings, get_ui_lang,
    set_ui_lang, set_trans_lang, set_category,
    get_next_word_for_user, find_word, get_quiz_options,
)
from bot.keyboards import (
    t,
    main_menu, settings_menu,
    ui_language_menu, translation_language_menu, category_menu,
    audio_button, quiz_keyboard,
)

bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

# Quiz тухайн session-д хадгална
QUIZ_STATE: dict = {}

# ──────────────────────────────────────────────
#  UI текстүүд — 3 хэлээр
# ──────────────────────────────────────────────
TEXTS = {
    "mn": {
        "welcome": (
            "🇲🇳 Тавтай морилно уу!\n"
            "Интерфейсийн хэл болон орчуулгын хэлийг өөрчлөхийг хүсвэл «Тохиргоо» руу орно уу.\n\n"
            "🇷🇺 Добро пожаловать!\n"
            "Для смены языка перейдите в «Настройки».\n\n"
            "🇬🇧 Welcome!\n"
            "To change the language, go to Settings."
        ),
        "start":          "Үйлдлээ сонгоно уу:",
        "settings":       "Тохиргоо:",
        "choose_ui":      "Интерфейсийн хэлээ сонгоно уу:",
        "choose_trans":   "Орчуулгын хэлээ сонгоно уу:",
        "choose_category":"Үгийн ангиллаа сонгоно уу:",
        "saved":          "✅ Хадгалагдлаа.",
        "not_found":      "❌ Энэ үг мэдээллийн санд олдсонгүй.",
        "no_words":       "⚠️ Сонгосон ангилалд үг олдсонгүй.",
        "word":           "📖 Үг",
        "translation":    "🔤 Орчуулга",
        "example":        "💬 Жишээ",
        "about": (
            "🤖 Энэ бол орос хэл сурахад зориулсан Telegram чатбот.\n\n"
            "✅ Үг сурах\n"
            "✅ Тест өгөх\n"
            "✅ Дуудлага сонсох\n"
            "✅ Үг хайх\n\n"
            "📚 Ангилал: Ерөнхий, Инженер, Эдийн засаг"
        ),
        "help": (
            "📖 Хэрхэн ашиглах вэ:\n\n"
            "1️⃣ Тохиргоо → интерфейс болон орчуулгын хэлээ сонгоно\n"
            "2️⃣ Үгийн ангиллаа сонгоно\n"
            "3️⃣ «Үг сурах» дарна\n"
            "4️⃣ Мэдлэгээ «Тест»-ээр шалгана\n"
            "5️⃣ Чатад үг бичвэл орчуулга гарна"
        ),
        "quiz_question":  "Зөв орчуулгыг сонгоно уу:",
        "quiz_correct":   "✅ Зөв!",
        "quiz_wrong":     "❌ Буруу.",
        "correct_answer": "Зөв хариулт",
        "need_4_words":   "⚠️ Тест хийхэд сонгосон ангилалд дор хаяж 4 үг хэрэгтэй.",
    },
    "ru": {
        "welcome": (
            "🇲🇳 Тавтай морилно уу!\n"
            "Интерфейсийн хэл болон орчуулгын хэлийг өөрчлөхийг хүсвэл «Тохиргоо» руу орно уу.\n\n"
            "🇷🇺 Добро пожаловать!\n"
            "Для смены языка перейдите в «Настройки».\n\n"
            "🇬🇧 Welcome!\n"
            "To change the language, go to Settings."
        ),
        "start":          "Выберите действие:",
        "settings":       "Настройки:",
        "choose_ui":      "Выберите язык интерфейса:",
        "choose_trans":   "Выберите язык перевода:",
        "choose_category":"Выберите категорию слов:",
        "saved":          "✅ Сохранено.",
        "not_found":      "❌ Слово не найдено в базе.",
        "no_words":       "⚠️ Слова в выбранной категории не найдены.",
        "word":           "📖 Слово",
        "translation":    "🔤 Перевод",
        "example":        "💬 Пример",
        "about": (
            "🤖 Это Telegram-бот для изучения русских слов.\n\n"
            "✅ Учить слова\n"
            "✅ Проходить тесты\n"
            "✅ Слушать произношение\n"
            "✅ Искать слова\n\n"
            "📚 Категории: Общий, Инженерия, Экономика"
        ),
        "help": (
            "📖 Как пользоваться ботом:\n\n"
            "1️⃣ Настройки → выберите язык интерфейса и перевода\n"
            "2️⃣ Выберите категорию слов\n"
            "3️⃣ Нажмите «Учить слова»\n"
            "4️⃣ Проверьте знания через «Тест»\n"
            "5️⃣ Напишите слово в чат — получите перевод"
        ),
        "quiz_question":  "Выберите правильный перевод:",
        "quiz_correct":   "✅ Правильно!",
        "quiz_wrong":     "❌ Неправильно.",
        "correct_answer": "Правильный ответ",
        "need_4_words":   "⚠️ Для теста нужно минимум 4 слова в категории.",
    },
    "en": {
        "welcome": (
            "🇲🇳 Тавтай морилно уу!\n"
            "Интерфейсийн хэл болон орчуулгын хэлийг өөрчлөхийг хүсвэл «Тохиргоо» руу орно уу.\n\n"
            "🇷🇺 Добро пожаловать!\n"
            "Для смены языка перейдите в «Настройки».\n\n"
            "🇬🇧 Welcome!\n"
            "To change the language, go to Settings."
        ),
        "start":          "Choose an action:",
        "settings":       "Settings:",
        "choose_ui":      "Choose interface language:",
        "choose_trans":   "Choose translation language:",
        "choose_category":"Choose word category:",
        "saved":          "✅ Saved.",
        "not_found":      "❌ Word not found in the database.",
        "no_words":       "⚠️ No words found in the selected category.",
        "word":           "📖 Word",
        "translation":    "🔤 Translation",
        "example":        "💬 Example",
        "about": (
            "🤖 This is a Telegram bot for learning Russian words.\n\n"
            "✅ Learn words\n"
            "✅ Take quizzes\n"
            "✅ Listen to pronunciation\n"
            "✅ Search words\n\n"
            "📚 Categories: General, Engineering, Economics"
        ),
        "help": (
            "📖 How to use the bot:\n\n"
            "1️⃣ Settings → choose interface and translation language\n"
            "2️⃣ Choose a word category\n"
            "3️⃣ Press «Learn words»\n"
            "4️⃣ Check yourself with the Quiz\n"
            "5️⃣ Type a word in the chat to get a translation"
        ),
        "quiz_question":  "Choose the correct translation:",
        "quiz_correct":   "✅ Correct!",
        "quiz_wrong":     "❌ Wrong.",
        "correct_answer": "Correct answer",
        "need_4_words":   "⚠️ At least 4 words are needed in the selected category.",
    },
}


def tx(lang: str, key: str) -> str:
    """TEXTS сөвөөс мөр буцаана."""
    return TEXTS.get(lang, TEXTS["mn"]).get(key, key)


def get_translation(trans_lang: str, ru: str, mn: str | None, en: str | None) -> str:
    if trans_lang == "mn":
        return mn or "—"
    if trans_lang == "en":
        return en or "—"
    return ru


# ──────────────────────────────────────────────
#  Үг илгээх (карт хэлбэрт)
# ──────────────────────────────────────────────
async def send_word(message: Message, row) -> None:
    user_id   = message.from_user.id
    settings  = await get_user_settings(user_id)
    ui_lang   = settings["ui_lang"]
    trans_lang = settings["trans_lang"]

    ru         = row["ru"]
    translation = get_translation(trans_lang, ru, row["mn"], row["en"])
    example    = row["example_ru"] or "—"
    image_url  = row["image_url"]

    text = (
        f"{tx(ui_lang, 'word')}: *{ru}*\n\n"
        f"{tx(ui_lang, 'translation')}: {translation}\n\n"
        f"{tx(ui_lang, 'example')}: _{example}_"
    )

    kb = audio_button(ui_lang, ru)
    if image_url:
        await message.answer_photo(photo=image_url, caption=text,
                                   reply_markup=kb, parse_mode="Markdown")
    else:
        await message.answer(text, reply_markup=kb, parse_mode="Markdown")


# ══════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════

# ── /start ────────────────────────────────────
@dp.message(Command("start"))
async def start_handler(message: Message):
    uid = message.from_user.id
    await ensure_user(uid, message.from_user.username)
    ui_lang = await get_ui_lang(uid)
    await message.answer(tx(ui_lang, "welcome"), reply_markup=main_menu(ui_lang))
    await message.answer(tx(ui_lang, "start"))


# ── 📚 Үг сурах ───────────────────────────────
@dp.message(F.text.in_(["📚 Үг сурах", "📚 Учить слова", "📚 Learn words"]))
async def learn_handler(message: Message):
    uid      = message.from_user.id
    settings = await get_user_settings(uid)
    row      = await get_next_word_for_user(uid, settings["category"])
    if not row:
        await message.answer(tx(settings["ui_lang"], "no_words"))
        return
    await send_word(message, row)


# ── 🧪 Тест ───────────────────────────────────
@dp.message(F.text.in_(["🧪 Тест", "🧪 Тест", "🧪 Quiz"]))
async def quiz_handler(message: Message):
    uid      = message.from_user.id
    settings = await get_user_settings(uid)
    ui_lang  = settings["ui_lang"]
    rows     = await get_quiz_options(settings["category"], 4)

    if len(rows) < 4:
        await message.answer(tx(ui_lang, "need_4_words"))
        return

    correct     = random.choice(rows)
    correct_id  = correct["id"]
    trans_lang  = settings["trans_lang"]

    options = [(r["id"], get_translation(trans_lang, r["ru"], r["mn"], r["en"])) for r in rows]
    random.shuffle(options)

    QUIZ_STATE[uid] = {
        "correct_id": correct_id,
        "ru":         correct["ru"],
        "answer":     get_translation(trans_lang, correct["ru"], correct["mn"], correct["en"]),
    }

    text = f"{tx(ui_lang, 'word')}: *{correct['ru']}*\n\n{tx(ui_lang, 'quiz_question')}"
    await message.answer(text, reply_markup=quiz_keyboard(options), parse_mode="Markdown")


@dp.callback_query(F.data.startswith("quiz:"))
async def quiz_callback(call: CallbackQuery):
    uid = call.from_user.id
    if uid not in QUIZ_STATE:
        await call.answer()
        return

    state      = QUIZ_STATE.pop(uid)
    chosen_id  = int(call.data.split(":")[1])
    ui_lang    = await get_ui_lang(uid)

    if chosen_id == state["correct_id"]:
        await call.message.answer(tx(ui_lang, "quiz_correct"))
    else:
        await call.message.answer(
            f"{tx(ui_lang, 'quiz_wrong')}\n"
            f"{tx(ui_lang, 'correct_answer')}: *{state['ru']}* — {state['answer']}",
            parse_mode="Markdown",
        )
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.answer()


# ── 🔊 Audio ──────────────────────────────────
@dp.callback_query(F.data.startswith("audio:"))
async def audio_callback(call: CallbackQuery):
    word = call.data.split(":", 1)[1]
    try:
        tts = gTTS(text=word, lang="ru")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            path = tmp.name
        tts.save(path)
        await call.message.answer_audio(audio=FSInputFile(path), title=word)
        try:
            os.remove(path)
        except OSError:
            pass
    except Exception as e:
        await call.message.answer(f"Audio error: {e}")
    await call.answer()


# ── ⚙️ Тохиргоо ───────────────────────────────
@dp.message(F.text.in_(["⚙️ Тохиргоо", "⚙️ Настройки", "⚙️ Settings"]))
async def settings_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)
    await message.answer(tx(ui_lang, "settings"), reply_markup=settings_menu(ui_lang))


# ── 🌐 Интерфейсийн хэл ───────────────────────
@dp.message(F.text.in_(["🌐 Интерфейсийн хэл", "🌐 Язык интерфейса", "🌐 Interface language"]))
async def ui_lang_menu_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)
    await message.answer(tx(ui_lang, "choose_ui"), reply_markup=ui_language_menu(ui_lang))


@dp.message(F.text.in_(["🇲🇳 Монгол", "🇷🇺 Русский", "🇬🇧 English"]))
async def set_ui_lang_handler(message: Message):
    mapping = {"🇲🇳 Монгол": "mn", "🇷🇺 Русский": "ru", "🇬🇧 English": "en"}
    new_lang = mapping[message.text]
    await set_ui_lang(message.from_user.id, new_lang)
    await message.answer(tx(new_lang, "saved"), reply_markup=main_menu(new_lang))


# ── 🔤 Орчуулгын хэл ──────────────────────────
@dp.message(F.text.in_(["🔤 Орчуулгын хэл", "🔤 Язык перевода", "🔤 Translation language"]))
async def trans_lang_menu_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)
    await message.answer(tx(ui_lang, "choose_trans"), reply_markup=translation_language_menu(ui_lang))


@dp.message(F.text.in_(["🇲🇳 Монгол хэл", "🇬🇧 English language"]))
async def set_trans_lang_handler(message: Message):
    mapping = {"🇲🇳 Монгол хэл": "mn", "🇬🇧 English language": "en"}
    await set_trans_lang(message.from_user.id, mapping[message.text])
    ui_lang = await get_ui_lang(message.from_user.id)
    await message.answer(tx(ui_lang, "saved"), reply_markup=main_menu(ui_lang))


# ── 📂 Ангилал ────────────────────────────────
@dp.message(F.text.in_(["📂 Үгийн ангилал", "📂 Категория слов", "📂 Word category"]))
async def category_menu_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)
    await message.answer(tx(ui_lang, "choose_category"), reply_markup=category_menu(ui_lang))


@dp.message(F.text.in_(["📚 Ерөнхий", "⚙️ Инженер", "💰 Эдийн засаг"]))
async def set_category_handler(message: Message):
    mapping = {
        "📚 Ерөнхий":    "general",
        "⚙️ Инженер":    "engineering",
        "💰 Эдийн засаг":"economics",
    }
    await set_category(message.from_user.id, mapping[message.text])
    ui_lang = await get_ui_lang(message.from_user.id)
    await message.answer(tx(ui_lang, "saved"), reply_markup=main_menu(ui_lang))


# ── ℹ️ About ──────────────────────────────────
@dp.message(F.text.in_(["ℹ️ Ботын тухай", "ℹ️ О боте", "ℹ️ About"]))
async def about_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)
    await message.answer(tx(ui_lang, "about"))


# ── 📖 Help ───────────────────────────────────
@dp.message(F.text.in_(["📖 Хэрхэн ашиглах вэ", "📖 Как пользоваться ботом", "📖 How to use"]))
async def help_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)
    await message.answer(tx(ui_lang, "help"))


# ── ⬅️ Буцах ──────────────────────────────────
@dp.message(F.text.in_(["⬅️ Буцах", "⬅️ Назад", "⬅️ Back"]))
async def back_handler(message: Message):
    ui_lang = await get_ui_lang(message.from_user.id)
    await message.answer(tx(ui_lang, "start"), reply_markup=main_menu(ui_lang))


# ── Шууд үг хайх ──────────────────────────────
@dp.message()
async def word_lookup_handler(message: Message):
    text = (message.text or "").strip()
    if not text:
        return
    row = await find_word(text)
    uid = message.from_user.id
    if not row:
        ui_lang = await get_ui_lang(uid)
        await message.answer(tx(ui_lang, "not_found"))
        return
    await send_word(message, row)


# ══════════════════════════════════════════════
#  Эхлүүлэх
# ══════════════════════════════════════════════
async def main():
    await init_db()
    imported = await import_words_from_csv("words.csv")
    if imported:
        print(f"✅ {imported} үг импортлогдлоо.")
    else:
        print("ℹ️  Үг импортлогдоогүй (аль хэдийн байгаа эсвэл файл олдсонгүй).")
    try:
        await dp.start_polling(bot)
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())