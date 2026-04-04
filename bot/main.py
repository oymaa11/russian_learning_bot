import asyncio
import random
from gtts import gTTS
import tempfile

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
)

from bot.config import BOT_TOKEN
from bot.db import (
    init_db,
    ensure_user,
    get_user,
    set_user_ui_lang,
    set_user_trans_lang,
    set_user_level,
    set_user_category,
    get_user_level,
    get_user_trans_lang,
    get_user_ui_lang,
    get_user_category,
    get_next_word_for_user,
    get_random_word_for_level,
    get_quiz_options,
    add_weekly_score,
    import_words_from_csv,
    get_leaderboard,
    get_user_rank,
    ensure_user_stats,
    increment_words_learned,
    update_quiz_stats,
    get_user_stats,
    get_quiz_sentence_options,
    find_word,
    get_weak_quiz_options,
    improve_weak_word,
    seed_grammar,
    get_grammar_topics,
    get_grammar_topic,
    get_grammar_quiz,
    get_grammar_quiz_answer,
)
from bot.keyboards import (
    kb_ui_language,
    kb_translation_language,
    kb_level,
    kb_category,
    kb_reply_menu,
    kb_settings_menu,
    kb_ui_language_settings,
    kb_translation_language_settings,
    kb_level_settings,
    kb_category_settings,
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

TEXTS = {
    "mn": {
        "start": "Сайн байна уу! 👋\n\nЭхлээд интерфейсийн хэлээ сонгоорой:",
        "ui_saved": "✅ Интерфейсийн хэл хадгалагдлаа.",
        "translation_lang": "Орчуулгын хэлээ сонгоорой (MN/EN):",
        "level": "Түвшнээ сонгоорой (A1–B2):",
        "category": "Үгийн төрлөө сонгоорой:",
        "category_saved": "✅ Ангилал хадгалагдлаа.\n\nОдоо доорх цэснээс сонгоорой 👇",
        "settings": "Интерфейсийн хэлээ сонгоорой:",
        "settings_menu": "⚙️ Тохиргоо\n\nӨөрчлөх зүйлээ сонгоно уу:",
        "saved_short": "✅ Тохиргоо шинэчлэгдлээ.",
        "not_registered": "Та бүртгэлгүй байна. /start гэж эхлүүлнэ үү.",
        "need_start": "Эхлээд /start хийж тохиргоогоо хийнэ үү.",
        "need_trans_lang": "Эхлээд /start хийж орчуулгын хэлээ сонгоорой.",
        "need_category": "Эхлээд үгийн ангиллаа сонгоорой.",
        "no_words": "Энэ түвшин, ангилалд үг алга байна.",
        "new_done": "✅ {level} түвшний {category_name} ангиллын шинэ үгс дууслаа.",
        "quiz_start": "🧪 Тест эхэллээ! Нийт 5 асуулт байна.",
        "profile_title": "👤 Таны профайл",
        "profile_id": "Telegram ID",
        "profile_username": "Username",
        "profile_ui_lang": "Интерфейсийн хэл",
        "profile_trans_lang": "Орчуулгын хэл",
        "profile_level": "Түвшин",
        "profile_category": "Үгийн ангилал",
        "profile_created": "Бүртгүүлсэн огноо",
        "new_word_title": "📚 Шинэ үг ({level})",
        "review_title": "🔁 Давтлага ({level})",
        "quiz_not_enough": "Тест хийхэд хангалттай үг алга байна (дор хаяж 4 үг хэрэгтэй).",
        "quiz_q_translate": "Орчуулгыг сонго:",
        "quiz_q_russian": "Орос үгийг сонго:",
        "quiz_finished": "🏁 Тест дууслаа!\nЗөв: {correct}/{total}\nОноо: +{score}\n\n🏆 Оноо 7 хоногийн тэмцээнд нэмэгдлээ.",
        "quiz_correct": "✅ Зөв!",
        "quiz_wrong": "❌ Буруу",
        "quiz_expired": "Тест дууссан эсвэл эхлээгүй байна. 🧪 товчийг дарна уу.",
        "placement_later": "Placement test-ийг 2-р шатанд нэмнэ.\n\nОдоохондоо A1–B2-оос нэгийг сонгоорой:",
        "cat_general": "ерөнхий",
        "cat_engineering": "инженер",
        "cat_economics": "эдийн засаг",
        "stats_title": "📊 Таны статистик",
        "stats_words": "Сурсан үг",
        "stats_quizzes": "Хийсэн тест",
        "stats_correct": "Зөв хариулт",
        "stats_score": "Нийт оноо",
        "lb_title": "🏆 7 хоногийн шилдгүүд",
        "lb_place": "Таны байр",
        "lb_score": "Таны оноо",
        "lb_empty": "Та одоогоор оноо аваагүй байна.",
        "no_weak_words": "Та одоогоор алдаатай үггүй байна 👍",
        "weak_words_title": "❗ Танд хэцүү байгаа үгс:\n\n",
        "quiz_q_sentence": "Өгүүлбэрт тохирох үгийг сонго:",
        "word_found": "🔎 Олдлоо",
        "word_not_found": "Уучлаарай, энэ үг одоохондоо манай санд алга.",
        "word_level": "Түвшин",
        "word_category": "Ангилал",
        "word_example": "Жишээ",
        "weak_words_title": "❗ Танд хэцүү байгаа үгс:\n\n",
        "no_weak_words": "Та одоогоор алдаатай үггүй байна 👍",
        "weak_quiz_start": "🧪 Алдаатай үгсийн тест эхэллээ!",
        "weak_quiz_not_enough": "Алдаатай үгсийн тест хийхэд дор хаяж 4 үг хэрэгтэй.",
        "weak_quiz_button": "🧪 Алдаатай үгсийн тест",
        "grammar_choose": "📖 Дүрмийн сэдвээ сонгоно уу:",
        "grammar_not_found": "Дүрмийн сэдэв олдсонгүй.",
        "grammar_quiz_btn": "🧪 Жижиг тест",
        "grammar_quiz_not_found": "Дүрмийн тест олдсонгүй.",
        "grammar_error": "Алдаа гарлаа.",
    },
    "ru": {
        "start": "Привет! 👋\n\nСначала выберите язык интерфейса:",
        "ui_saved": "✅ Язык интерфейса сохранён.",
        "translation_lang": "Выберите язык перевода (MN/EN):",
        "level": "Выберите уровень (A1–B2):",
        "category": "Выберите тип лексики:",
        "category_saved": "✅ Категория сохранена.\n\nТеперь можно начать обучение 👇",
        "settings": "Выберите язык интерфейса:",
        "settings_menu": "⚙️ Настройки\n\nВыберите, что хотите изменить:",
        "saved_short": "✅ Настройка обновлена.",
        "not_registered": "Вы не зарегистрированы. Нажмите /start.",
        "need_start": "Сначала выполните настройку: /start.",
        "need_trans_lang": "Сначала выберите язык перевода: /start.",
        "need_category": "Сначала выберите категорию слов.",
        "no_words": "Для этого уровня и категории нет слов.",
        "new_done": "✅ Новые слова уровня {level} в категории «{category_name}» закончились.",
        "quiz_start": "🧪 Тест начался! Вопросов: 5.",
        "profile_title": "👤 Ваш профиль",
        "profile_id": "Telegram ID",
        "profile_username": "Username",
        "profile_ui_lang": "Язык интерфейса",
        "profile_trans_lang": "Язык перевода",
        "profile_level": "Уровень",
        "profile_category": "Категория слов",
        "profile_created": "Дата регистрации",
        "new_word_title": "📚 Новое слово ({level})",
        "review_title": "🔁 Повторение ({level})",
        "quiz_not_enough": "Недостаточно слов для теста (нужно минимум 4).",
        "quiz_q_translate": "Выберите перевод:",
        "quiz_q_russian": "Выберите русское слово:",
        "quiz_finished": "🏁 Тест завершён!\nПравильно: {correct}/{total}\nОчки: +{score}\n\n🏆 Очки добавлены в недельное соревнование.",
        "quiz_correct": "✅ Верно!",
        "quiz_wrong": "❌ Неверно",
        "quiz_expired": "Тест уже завершён или не запущен. Нажмите 🧪.",
        "placement_later": "Placement test будет добавлен во 2-й фазе.\n\nПока выберите уровень A1–B2:",
        "cat_general": "общая лексика",
        "cat_engineering": "инженерная лексика",
        "cat_economics": "экономическая лексика",
        "stats_title": "📊 Ваша статистика",
        "stats_words": "Изучено слов",
        "stats_quizzes": "Пройдено тестов",
        "stats_correct": "Правильных ответов",
        "stats_score": "Общие очки",
        "lb_title": "🏆 Топ игроков недели",
        "lb_place": "Ваше место",
        "lb_score": "Ваши очки",
        "lb_empty": "Вы пока не набрали очков.",
        "weak": "❗ Сложные слова",
        "no_weak_words": "У вас пока нет сложных слов 👍",
        "weak_words_title": "❗ Сложные для вас слова:\n\n",
        "quiz_q_sentence": "Выберите слово, которое подходит в предложение:",
        "word_found": "🔎 Найдено",
        "word_not_found": "Извините, этого слова пока нет в нашей базе.",
        "word_level": "Уровень",
        "word_category": "Категория",
        "word_example": "Пример",
        "weak_words_title": "❗ Сложные для вас слова:\n\n",
        "no_weak_words": "У вас пока нет сложных слов 👍",
        "weak_quiz_start": "🧪 Тест по сложным словам начался!",
        "weak_quiz_not_enough": "Для теста по сложным словам нужно минимум 4 слова.",
        "weak_quiz_button": "🧪 Тест по сложным словам",
        "grammar_choose": "📖 Выберите грамматическую тему:",
        "grammar_not_found": "Грамматическая тема не найдена.",
        "grammar_quiz_btn": "🧪 Мини-тест",
        "grammar_quiz_not_found": "Грамматический тест не найден.",
        "grammar_error": "Произошла ошибка.",
    },
    "en": {
        "start": "Hello! 👋\n\nFirst, choose the interface language:",
        "ui_saved": "✅ Interface language saved.",
        "translation_lang": "Choose translation language (MN/EN):",
        "level": "Choose your level (A1–B2):",
        "category": "Choose a vocabulary category:",
        "category_saved": "✅ Category saved.\n\nNow you can start learning 👇",
        "settings": "Choose the interface language:",
        "settings_menu": "⚙️ Settings\n\nChoose what you want to change:",
        "saved_short": "✅ Setting updated.",
        "not_registered": "You are not registered. Press /start.",
        "need_start": "Please complete setup first: /start.",
        "need_trans_lang": "Please choose translation language first: /start.",
        "need_category": "Please choose a word category first.",
        "no_words": "There are no words for this level and category.",
        "new_done": "✅ New words for level {level} in category '{category_name}' are finished.",
        "quiz_start": "🧪 Quiz started! Total questions: 5.",
        "profile_title": "👤 Your profile",
        "profile_id": "Telegram ID",
        "profile_username": "Username",
        "profile_ui_lang": "Interface language",
        "profile_trans_lang": "Translation language",
        "profile_level": "Level",
        "profile_category": "Word category",
        "profile_created": "Registration date",
        "new_word_title": "📚 New word ({level})",
        "review_title": "🔁 Review ({level})",
        "quiz_not_enough": "Not enough words for a quiz (at least 4 required).",
        "quiz_q_translate": "Choose the translation:",
        "quiz_q_russian": "Choose the Russian word:",
        "quiz_finished": "🏁 Quiz finished!\nCorrect: {correct}/{total}\nScore: +{score}\n\n🏆 Points were added to the weekly competition.",
        "quiz_correct": "✅ Correct!",
        "quiz_wrong": "❌ Wrong",
        "quiz_expired": "The quiz has finished or was not started. Press 🧪.",
        "placement_later": "Placement test will be added in phase 2.\n\nFor now, choose a level from A1 to B2:",
        "cat_general": "general",
        "cat_engineering": "engineering",
        "cat_economics": "economics",
        "stats_title": "📊 Your statistics",
        "stats_words": "Words learned",
        "stats_quizzes": "Quizzes taken",
        "stats_correct": "Correct answers",
        "stats_score": "Total score",
        "lb_title": "🏆 Weekly top players",
        "lb_place": "Your place",
        "lb_score": "Your score",
        "lb_empty": "You have no points yet.",
        "weak": "❗ Difficult words",
        "no_weak_words": "У вас пока нет сложных слов 👍",
        "weak_words_title": "❗ Words you struggle with:\n\n",
        "quiz_q_sentence": "Choose the word that fits the sentence:",
        "word_found": "🔎 Found",
        "word_not_found": "Sorry, this word is not in our database yet.",
        "word_level": "Level",
        "word_category": "Category",
        "word_example": "Example",
        "weak_words_title": "❗ Words you struggle with:\n\n",
        "no_weak_words": "You have no difficult words yet 👍",
        "weak_quiz_start": "🧪 Difficult words quiz started!",
        "weak_quiz_not_enough": "At least 4 difficult words are required for this quiz.",
        "weak_quiz_button": "🧪 Difficult words quiz",
        "grammar_choose": "📖 Choose a grammar topic:",
        "grammar_not_found": "Grammar topic not found.",
        "grammar_quiz_btn": "🧪 Mini quiz",
        "grammar_quiz_not_found": "Grammar quiz not found.",
        "grammar_error": "An error occurred.",
    },
}

QUIZ_STATE: dict[int, dict] = {}
SEARCH_MODE: set[int] = set()

async def tr(user_id: int, key: str, **kwargs) -> str:
    ui_lang = await get_user_ui_lang(user_id) or "ru"
    text = TEXTS.get(ui_lang, TEXTS["ru"]).get(key, key)
    return text.format(**kwargs)


async def get_category_name(user_id: int, category: str) -> str:
    mapping = {
        "general": await tr(user_id, "cat_general"),
        "engineering": await tr(user_id, "cat_engineering"),
        "economics": await tr(user_id, "cat_economics"),
    }
    return mapping.get(category, category)


def format_word_text(
    title: str,
    ru: str,
    mn: str | None,
    en: str | None,
    trans_lang: str,
) -> str:
    if trans_lang == "mn":
        return f"{title}\n🇷🇺 {ru}\n🇲🇳 {mn or '—'}"
    return f"{title}\n🇷🇺 {ru}\n🇬🇧 {en or '—'}"


async def main():
    await init_db()
    added = await import_words_from_csv("words.csv")
    print(f"Imported words: {added}")
    await seed_grammar()
    await dp.start_polling(bot)


@dp.message(Command("start"))
async def start(message: Message):
    await ensure_user(message.from_user.id, message.from_user.username)
    await ensure_user_stats(message.from_user.id)
    await message.answer(
        await tr(message.from_user.id, "start"),
        reply_markup=kb_ui_language(),
    )


# ---------------- ONBOARDING ----------------

@dp.callback_query(F.data.startswith("ui:"))
async def on_ui_lang(call: CallbackQuery):
    ui_lang = call.data.split(":", 1)[1]
    await set_user_ui_lang(call.from_user.id, ui_lang)
    await call.answer()

    await call.message.edit_text(
        await tr(call.from_user.id, "translation_lang"),
        reply_markup=kb_translation_language(),
    )


@dp.callback_query(F.data.startswith("tr:"))
async def on_trans_lang(call: CallbackQuery):
    tr_lang = call.data.split(":", 1)[1]
    await set_user_trans_lang(call.from_user.id, tr_lang)
    await call.answer()

    await call.message.edit_text(
        await tr(call.from_user.id, "level"),
        reply_markup=kb_level(),
    )


@dp.callback_query(F.data.startswith("lv:"))
async def on_level(call: CallbackQuery):
    lv = call.data.split(":", 1)[1]
    await call.answer()

    if lv == "test":
        await call.message.edit_text(
            await tr(call.from_user.id, "placement_later"),
            reply_markup=kb_level(),
        )
        return

    await set_user_level(call.from_user.id, lv)
    await call.message.edit_text(
        await tr(call.from_user.id, "category"),
        reply_markup=kb_category(),
    )


@dp.callback_query(F.data.startswith("cat:"))
async def on_category(call: CallbackQuery):
    category = call.data.split(":", 1)[1]
    await set_user_category(call.from_user.id, category)
    await call.answer()

    ui_lang = await get_user_ui_lang(call.from_user.id) or "ru"
    await call.message.answer(
        await tr(call.from_user.id, "category_saved"),
        reply_markup=kb_reply_menu(ui_lang),
    )


# ---------------- SETTINGS ----------------

@dp.callback_query(F.data == "set:ui")
async def set_ui_handler(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        await tr(call.from_user.id, "settings"),
        reply_markup=kb_ui_language_settings(),
    )


@dp.callback_query(F.data == "set:tr")
async def set_tr_handler(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        await tr(call.from_user.id, "translation_lang"),
        reply_markup=kb_translation_language_settings(),
    )


@dp.callback_query(F.data == "set:level")
async def set_level_handler(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        await tr(call.from_user.id, "level"),
        reply_markup=kb_level_settings(),
    )


@dp.callback_query(F.data == "set:category")
async def set_category_handler(call: CallbackQuery):
    await call.answer()
    await call.message.answer(
        await tr(call.from_user.id, "category"),
        reply_markup=kb_category_settings(),
    )


@dp.callback_query(F.data.startswith("sui:"))
async def settings_ui_lang(call: CallbackQuery):
    ui_lang = call.data.split(":", 1)[1]
    await set_user_ui_lang(call.from_user.id, ui_lang)
    await call.answer()

    # 1. Доод reply menu-г шинэ хэлээр refresh хийнэ
    await call.message.answer(
        await tr(call.from_user.id, "saved_short"),
        reply_markup=kb_reply_menu(ui_lang),
    )

    # 2. Settings inline menu-г бас дахин харуулна
    await call.message.answer(
        await tr(call.from_user.id, "settings_menu"),
        reply_markup=kb_settings_menu(),
    )

@dp.callback_query(F.data.startswith("str:"))
async def settings_trans_lang(call: CallbackQuery):
    tr_lang = call.data.split(":", 1)[1]
    await set_user_trans_lang(call.from_user.id, tr_lang)
    await call.answer()
    await call.message.answer(
        await tr(call.from_user.id, "saved_short"),
        reply_markup=kb_settings_menu(),
    )


@dp.callback_query(F.data.startswith("slv:"))
async def settings_level(call: CallbackQuery):
    lv = call.data.split(":", 1)[1]
    await set_user_level(call.from_user.id, lv)
    await call.answer()
    await call.message.answer(
        await tr(call.from_user.id, "saved_short"),
        reply_markup=kb_settings_menu(),
    )


@dp.callback_query(F.data.startswith("scat:"))
async def settings_category(call: CallbackQuery):
    category = call.data.split(":", 1)[1]
    await set_user_category(call.from_user.id, category)
    await call.answer()
    await call.message.answer(
        await tr(call.from_user.id, "saved_short"),
        reply_markup=kb_settings_menu(),
    )


# ---------------- MENU ----------------

@dp.message(F.text.startswith("📚"))
async def btn_newword(message: Message):
    await new_word_handler(message)


@dp.message(F.text.startswith("🔁"))
async def btn_review(message: Message):
    await review_handler(message)


@dp.message(F.text.startswith("🧪"))
async def btn_quiz(message: Message):
    await quiz_handler(message)


@dp.message(F.text.startswith("👤"))
async def btn_profile(message: Message):
    await profile_handler(message)


@dp.message(F.text.startswith("⚙️"))
async def btn_settings(message: Message):
    await message.answer(
        await tr(message.from_user.id, "settings_menu"),
        reply_markup=kb_settings_menu(),
    )


@dp.message(F.text.startswith("🏆"))
async def btn_leaderboard(message: Message):
    level = await get_user_level(message.from_user.id)
    if not level:
        await message.answer(await tr(message.from_user.id, "need_start"))
        return

    board = await get_leaderboard(level)
    rank, score = await get_user_rank(message.from_user.id, level)

    text = f"{await tr(message.from_user.id, 'lb_title')}\n\n"

    pos = 1
    for username, sc in board:
        name = username if username else "user"
        text += f"{pos}. @{name} — {sc}\n"
        pos += 1

    text += "\n"

    if rank:
        text += f"👤 {await tr(message.from_user.id, 'lb_place')}: {rank}\n"
        text += f"⭐ {await tr(message.from_user.id, 'lb_score')}: {score}"
    else:
        text += await tr(message.from_user.id, "lb_empty")

    await message.answer(text)


@dp.message(F.text.startswith("📈"))
async def btn_stats(message: Message):
    await stats_handler(message)


@dp.message(Command("stats"))
async def stats_handler(message: Message):
    words_learned, quizzes_taken, correct_answers, total_score = await get_user_stats(message.from_user.id)

    await message.answer(
        f"{await tr(message.from_user.id, 'stats_title')}\n\n"
        f"📚 {await tr(message.from_user.id, 'stats_words')}: {words_learned}\n"
        f"🧪 {await tr(message.from_user.id, 'stats_quizzes')}: {quizzes_taken}\n"
        f"✅ {await tr(message.from_user.id, 'stats_correct')}: {correct_answers}\n"
        f"⭐ {await tr(message.from_user.id, 'stats_score')}: {total_score}"
    )


@dp.message(Command("profile"))
async def profile_handler(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer(await tr(message.from_user.id, "not_registered"))
        return

    category_name = await get_category_name(
        message.from_user.id,
        user["preferred_category"] or "general",
    )

    await message.answer(
        f"{await tr(message.from_user.id, 'profile_title')}\n"
        f"- {await tr(message.from_user.id, 'profile_id')}: {user['telegram_id']}\n"
        f"- {await tr(message.from_user.id, 'profile_username')}: @{user['username']}\n"
        f"- {await tr(message.from_user.id, 'profile_ui_lang')}: {user['ui_lang']}\n"
        f"- {await tr(message.from_user.id, 'profile_trans_lang')}: {user['trans_lang']}\n"
        f"- {await tr(message.from_user.id, 'profile_level')}: {user['level']}\n"
        f"- {await tr(message.from_user.id, 'profile_category')}: {category_name}\n"
        f"- {await tr(message.from_user.id, 'profile_created')}: {user['created_at']}\n"
    )


@dp.message(Command("newword"))
async def new_word_handler(message: Message):
    level = await get_user_level(message.from_user.id)
    if not level:
        await message.answer(await tr(message.from_user.id, "need_start"))
        return

    category = await get_user_category(message.from_user.id)
    if not category:
        await message.answer(await tr(message.from_user.id, "need_category"))
        return

    word = await get_next_word_for_user(message.from_user.id, level, category)
    if not word:
        category_name = await get_category_name(message.from_user.id, category)
        await message.answer(
            await tr(
                message.from_user.id,
                "new_done",
                level=level,
                category_name=category_name,
            )
        )
        return

    trans_lang = await get_user_trans_lang(message.from_user.id) or "mn"
    ru, mn, en, _image_url, example_ru = word
    title = await tr(message.from_user.id, "new_word_title", level=level)
    text = format_word_text(title, ru, mn, en, trans_lang)
    if example_ru:
        text += f"\n\n💬 {example_ru}"

    await increment_words_learned(message.from_user.id, 1)
    await message.answer(text)


@dp.message(Command("review"))
async def review_handler(message: Message):
    level = await get_user_level(message.from_user.id)
    if not level:
        await message.answer(await tr(message.from_user.id, "need_start"))
        return

    category = await get_user_category(message.from_user.id)
    if not category:
        await message.answer(await tr(message.from_user.id, "need_category"))
        return

    row = await get_random_word_for_level(level, category)
    if not row:
        await message.answer(await tr(message.from_user.id, "no_words"))
        return

    trans_lang = await get_user_trans_lang(message.from_user.id) or "mn"
    ru, mn, en, _image_url, example_ru = row
    title = await tr(message.from_user.id, "review_title", level=level)
    text = format_word_text(title, ru, mn, en, trans_lang)
    if example_ru:
        text += f"\n\n💬 {example_ru}"
    await message.answer(text)


@dp.message(Command("quiz"))
async def quiz_handler(message: Message):
    level = await get_user_level(message.from_user.id)
    if not level:
        await message.answer(await tr(message.from_user.id, "need_start"))
        return

    category = await get_user_category(message.from_user.id)
    if not category:
        await message.answer(await tr(message.from_user.id, "need_category"))
        return

    trans_lang = await get_user_trans_lang(message.from_user.id)
    if not trans_lang:
        await message.answer(await tr(message.from_user.id, "need_trans_lang"))
        return

    QUIZ_STATE[message.from_user.id] = {
        "level": level,
        "category": category,
        "trans_lang": trans_lang,
        "q_index": 0,
        "correct": 0,
        "total": 5,
    }

    await message.answer(await tr(message.from_user.id, "quiz_start"))
    await send_next_quiz_question(message.chat.id, message.from_user.id)


async def send_next_quiz_question(chat_id: int, user_id: int):
    st = QUIZ_STATE[user_id]
    level = st["level"]
    category = st["category"]
    trans_lang = st["trans_lang"]
    q_index = st["q_index"]

    options = await get_quiz_options(level, category, 4)
    if len(options) < 4:
        await bot.send_message(chat_id, await tr(user_id, "quiz_not_enough"))
        QUIZ_STATE.pop(user_id, None)
        return

    direction = random.choice([0, 1, 2])

    def tr_text(row):
        return row[2] if trans_lang == "mn" else row[3]

    if direction == 2:
        sentence_rows = await get_quiz_sentence_options(level, category, 4)
        if len(sentence_rows) >= 4:
            correct = random.choice(sentence_rows)
            correct_id, ru, mn, en, example_ru = correct

            sentence_text = example_ru.replace(ru, "______", 1)

            question_text = (
                f"🧪 {q_index + 1}/5 ({level})\n\n"
                f"{sentence_text}\n\n"
                f"{await tr(user_id, 'quiz_q_sentence')}"
            )

            answers = [(r[0], r[1]) for r in sentence_rows]

            kb = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=a[1], callback_data=f"qa:{correct_id}:{a[0]}")]
                    for a in answers
                ]
            )

            await bot.send_message(chat_id, question_text, reply_markup=kb)
            return

    # хуучин 2 төрлийн асуулт
    correct = random.choice(options)
    correct_id, ru, mn, en = correct

    if direction == 0:
        question_text = (
            f"🧪 {q_index + 1}/5 ({level})\n\n"
            f"🇷🇺 {ru}\n\n"
            f"{await tr(user_id, 'quiz_q_translate')}"
        )
        answers = [(r[0], tr_text(r)) for r in options]
    else:
        q_tr = tr_text(correct)
        question_text = (
            f"🧪 {q_index + 1}/5 ({level})\n\n"
            f"🌐 {q_tr}\n\n"
            f"{await tr(user_id, 'quiz_q_russian')}"
        )
        answers = [(r[0], r[1]) for r in options]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=a[1], callback_data=f"qa:{correct_id}:{a[0]}")]
            for a in answers
        ]
    )

    await bot.send_message(chat_id, question_text, reply_markup=kb)


@dp.callback_query(F.data.startswith("qa:"))
async def quiz_answer_callback(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id not in QUIZ_STATE:
        await call.answer(await tr(user_id, "quiz_expired"), show_alert=True)
        return

    _, correct_id_str, chosen_id_str = call.data.split(":")
    correct_id = int(correct_id_str)
    chosen_id = int(chosen_id_str)

    st = QUIZ_STATE[user_id]

    if chosen_id == correct_id:
        st["correct"] += 1
        await call.answer(await tr(user_id, "quiz_correct"))
    else:
        await call.answer(await tr(user_id, "quiz_wrong"))
        from bot.db import add_weak_word
        await add_weak_word(user_id, correct_id)

    st["q_index"] += 1

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if st["q_index"] >= st["total"]:
        score = st["correct"] * 10

        await add_weekly_score(
            user_id=user_id,
            level=st["level"],
            score_delta=score,
        )

        await update_quiz_stats(
            user_id=user_id,
            correct=st["correct"],
            score=score,
        )

        await call.message.answer(
            await tr(
                user_id,
                "quiz_finished",
                correct=st["correct"],
                total=st["total"],
                score=score,
            )
        )
        QUIZ_STATE.pop(user_id, None)
        return

    await send_next_quiz_question(call.message.chat.id, user_id)
@dp.message(F.text.startswith("❗"))
async def weak_words_handler(message: Message):
    from bot.db import get_weak_words

    words = await get_weak_words(message.from_user.id)

    if not words:
        await message.answer(await tr(message.from_user.id, "no_weak_words"))
        return

    text = await tr(message.from_user.id, "weak_words_title")

    for ru, mn, en in words:
        text += f"🇷🇺 {ru}\n🇲🇳 {mn}\n🇬🇧 {en}\n\n"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=await tr(message.from_user.id, "weak_quiz_button"),
                    callback_data="weakquiz:start",
                )
            ]
        ]
    )

    await message.answer(text, reply_markup=kb)
@dp.callback_query(F.data.startswith("voice:"))
async def pronunciation_handler(call: CallbackQuery):
    word = call.data.split(":", 1)[1]

    try:
        tts = gTTS(text=word, lang="ru")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            temp_path = tmp.name

        tts.save(temp_path)

        audio_file = FSInputFile(temp_path)

        await call.message.answer_audio(
            audio=audio_file,
            title=word,
        )

    except Exception:
        await call.message.answer(f"Voice error")

    finally:
        await call.answer()
@dp.callback_query(F.data == "weakquiz:start")
async def weak_quiz_start_handler(call: CallbackQuery):
    options = await get_weak_quiz_options(call.from_user.id, 4)

    if len(options) < 4:
        await call.answer()
        await call.message.answer(await tr(call.from_user.id, "weak_quiz_not_enough"))
        return

    trans_lang = await get_user_trans_lang(call.from_user.id)
    if not trans_lang:
        await call.answer()
        await call.message.answer(await tr(call.from_user.id, "need_trans_lang"))
        return

    QUIZ_STATE[call.from_user.id] = {
        "mode": "weak",
        "trans_lang": trans_lang,
        "q_index": 0,
        "correct": 0,
        "total": 5,
    }

    await call.answer()
    await call.message.answer(await tr(call.from_user.id, "weak_quiz_start"))
    await send_next_weak_quiz_question(call.message.chat.id, call.from_user.id)
async def send_next_weak_quiz_question(chat_id: int, user_id: int):
    st = QUIZ_STATE[user_id]
    trans_lang = st["trans_lang"]
    q_index = st["q_index"]

    options = await get_weak_quiz_options(user_id, 4)
    if len(options) < 4:
        await bot.send_message(chat_id, await tr(user_id, "weak_quiz_not_enough"))
        QUIZ_STATE.pop(user_id, None)
        return

    correct = random.choice(options)
    correct_id, ru, mn, en = correct

    def tr_text(row):
        return row[2] if trans_lang == "mn" else row[3]

    direction = random.choice([0, 1])

    if direction == 0:
        question_text = (
            f"🧪 {q_index + 1}/5\n\n"
            f"🇷🇺 {ru}\n\n"
            f"{await tr(user_id, 'quiz_q_translate')}"
        )
        answers = [(r[0], tr_text(r)) for r in options]
    else:
        q_tr = tr_text(correct)
        question_text = (
            f"🧪 {q_index + 1}/5\n\n"
            f"🌐 {q_tr}\n\n"
            f"{await tr(user_id, 'quiz_q_russian')}"
        )
        answers = [(r[0], r[1]) for r in options]

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=a[1], callback_data=f"wqa:{correct_id}:{a[0]}")]
            for a in answers
        ]
    )

    await bot.send_message(chat_id, question_text, reply_markup=kb)
@dp.callback_query(F.data.startswith("wqa:"))
async def weak_quiz_answer_callback(call: CallbackQuery):
    user_id = call.from_user.id
    if user_id not in QUIZ_STATE:
        await call.answer(await tr(user_id, "quiz_expired"), show_alert=True)
        return

    _, correct_id_str, chosen_id_str = call.data.split(":")
    correct_id = int(correct_id_str)
    chosen_id = int(chosen_id_str)

    st = QUIZ_STATE[user_id]

    if chosen_id == correct_id:
        st["correct"] += 1
        await improve_weak_word(user_id, correct_id)
        await call.answer(await tr(user_id, "quiz_correct"))
    else:
        await call.answer(await tr(user_id, "quiz_wrong"))

    st["q_index"] += 1

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    if st["q_index"] >= st["total"]:
        score = st["correct"] * 10

        await update_quiz_stats(
            user_id=user_id,
            correct=st["correct"],
            score=score,
        )

        await call.message.answer(
            await tr(
                user_id,
                "quiz_finished",
                correct=st["correct"],
                total=st["total"],
                score=score,
            )
        )
        QUIZ_STATE.pop(user_id, None)
        return

    await send_next_weak_quiz_question(call.message.chat.id, user_id)
@dp.message(F.text.startswith("🔎"))
async def btn_search(message: Message):

    SEARCH_MODE.add(message.from_user.id)

    ui_lang = await get_user_ui_lang(message.from_user.id) or "ru"

    if ui_lang == "mn":
        text = "Хайх үгээ явуулна уу:"
    elif ui_lang == "en":
        text = "Send the word you want to search:"
    else:
        text = "Напишите слово для поиска:"

    await message.answer(text)

@dp.message(F.text.startswith("📖"))
async def grammar_menu_handler(message: Message):
    topics = await get_grammar_topics()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title_ru, callback_data=f"gr:{topic_key}")]
            for topic_key, title_ru in topics
        ]
    )

    await message.answer(
        await tr(message.from_user.id, "grammar_choose"),
        reply_markup=kb,
    )
@dp.callback_query(F.data.startswith("gr:"))
async def grammar_topic_handler(call: CallbackQuery):
    topic_key = call.data.split(":", 1)[1]
    row = await get_grammar_topic(topic_key)

    if not row:
        await call.answer()
        await call.message.answer(await tr(call.from_user.id, "grammar_not_found"))
        return

    (
        title_ru,
        title_mn,
        title_en,
        theory_ru,
        theory_mn,
        theory_en,
        ex1,
        ex2,
    ) = row

    ui_lang = await get_user_ui_lang(call.from_user.id) or "ru"

    if ui_lang == "mn":
        title = title_mn
        theory = theory_mn
    elif ui_lang == "en":
        title = title_en
        theory = theory_en
    else:
        title = title_ru
        theory = theory_ru

    text = (
        f"{title}\n\n"
        f"📖 {theory}\n\n"
        f"💬 {ex1}\n"
        f"💬 {ex2}"
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=await tr(call.from_user.id, "grammar_quiz_btn"),
                    callback_data=f"grquiz:{topic_key}",
                )
            ]
        ]
    )

    await call.answer()
    await call.message.answer(text, reply_markup=kb)
@dp.callback_query(F.data.startswith("grquiz:"))
async def grammar_quiz_handler(call: CallbackQuery):
    topic_key = call.data.split(":", 1)[1]
    row = await get_grammar_quiz(topic_key)

    if not row:
        await call.answer()
        await call.message.answer(await tr(call.from_user.id, "grammar_quiz_not_found"))
        return

    quiz_id, question, option1, option2, option3, correct_option = row

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=option1, callback_data=f"gra:{quiz_id}:1")],
            [InlineKeyboardButton(text=option2, callback_data=f"gra:{quiz_id}:2")],
            [InlineKeyboardButton(text=option3, callback_data=f"gra:{quiz_id}:3")],
        ]
    )

    await call.answer()
    await call.message.answer(f"🧪 {question}", reply_markup=kb)
@dp.callback_query(F.data.startswith("gra:"))
async def grammar_answer_handler(call: CallbackQuery):
    _, quiz_id_str, chosen_str = call.data.split(":")
    quiz_id = int(quiz_id_str)
    chosen = int(chosen_str)

    correct = await get_grammar_quiz_answer(quiz_id)

    if correct is None:
        await call.answer(await tr(call.from_user.id, "grammar_error"), show_alert=True)
        return

    if chosen == correct:
        await call.answer(await tr(call.from_user.id, "quiz_correct"))
    else:
        await call.answer(await tr(call.from_user.id, "quiz_wrong"))

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
@dp.message(F.text)
async def dictionary_lookup(message: Message):
    user_id = message.from_user.id

    if user_id not in SEARCH_MODE:
        return

    SEARCH_MODE.remove(user_id)

    text = (message.text or "").strip()
    if not text:
        return

    row = await find_word(text)
    if not row:
        await message.answer(await tr(message.from_user.id, "word_not_found"))
        return

    level, category, ru, mn, en, example_ru = row
    category_name = await get_category_name(message.from_user.id, category)

    result_text = (
        f"{await tr(message.from_user.id, 'word_found')}\n\n"
        f"🇷🇺 {ru}\n"
        f"🇲🇳 {mn or '—'}\n"
        f"🇬🇧 {en or '—'}\n\n"
        f"📊 {await tr(message.from_user.id, 'word_level')}: {level}\n"
        f"📚 {await tr(message.from_user.id, 'word_category')}: {category_name}"
    )

    if example_ru:
        result_text += f"\n\n💬 {await tr(message.from_user.id, 'word_example')}: {example_ru}"

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔊 Произношение", callback_data=f"voice:{ru}")]
        ]
    )

    await message.answer(result_text, reply_markup=kb)
if __name__ == "__main__":
    asyncio.run(main())