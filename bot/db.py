import aiosqlite
import csv
import datetime
from pathlib import Path

DB_PATH = "bot.db"

CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    ui_lang TEXT,
    trans_lang TEXT,
    level TEXT,
    preferred_category TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    category TEXT NOT NULL,
    ru TEXT NOT NULL,
    mn TEXT,
    en TEXT,
    image_url TEXT,
    example_ru TEXT
);

CREATE TABLE IF NOT EXISTS weekly_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    level TEXT NOT NULL,
    week_id TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    UNIQUE(user_id, level, week_id)
);

CREATE TABLE IF NOT EXISTS user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    level TEXT NOT NULL,
    category TEXT NOT NULL,
    next_word_id INTEGER DEFAULT 1,
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, level, category)
);
CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY,
    words_learned INTEGER DEFAULT 0,
    quizzes_taken INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS grammar_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_key TEXT UNIQUE NOT NULL,

    title_ru TEXT NOT NULL,
    title_mn TEXT,
    title_en TEXT,

    theory_ru TEXT NOT NULL,
    theory_mn TEXT,
    theory_en TEXT,

    example1_ru TEXT,
    example2_ru TEXT
);

CREATE TABLE IF NOT EXISTS grammar_quiz (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_key TEXT NOT NULL,
    question_ru TEXT NOT NULL,
    option1 TEXT NOT NULL,
    option2 TEXT NOT NULL,
    option3 TEXT NOT NULL,
    correct_option INTEGER NOT NULL
);

"""

async def ensure_user_stats(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO user_stats (user_id) VALUES (?)",
            (user_id,),
        )
        await db.commit()


async def increment_words_learned(user_id: int, amount: int = 1) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO user_stats (user_id, words_learned)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                words_learned = words_learned + excluded.words_learned
            """,
            (user_id, amount),
        )
        await db.commit()


async def update_quiz_stats(user_id: int, correct: int, score: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO user_stats (user_id, quizzes_taken, correct_answers, total_score)
            VALUES (?, 1, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                quizzes_taken = quizzes_taken + 1,
                correct_answers = correct_answers + excluded.correct_answers,
                total_score = total_score + excluded.total_score
            """,
            (user_id, correct, score),
        )
        await db.commit()


async def get_user_stats(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT words_learned, quizzes_taken, correct_answers, total_score
            FROM user_stats
            WHERE user_id=?
            """,
            (user_id,),
        )
        row = await cur.fetchone()
        if not row:
            return (0, 0, 0, 0)
        return row
async def init_db() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.execute("""
CREATE TABLE IF NOT EXISTS weak_words (
    user_id INTEGER,
    word_id INTEGER,
    wrong_count INTEGER DEFAULT 1,
    PRIMARY KEY (user_id, word_id)
)
""")
        await db.commit()
async def add_weak_word(user_id: int, word_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        INSERT INTO weak_words (user_id, word_id, wrong_count)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, word_id)
        DO UPDATE SET wrong_count = wrong_count + 1
        """, (user_id, word_id))
        await db.commit()

async def import_words_from_csv(csv_path: str = "words.csv") -> int:
    path = Path(csv_path)
    if not path.exists():
        return 0

    rows = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            level = (r.get("level") or "").strip()
            category = (r.get("category") or "").strip()
            ru = (r.get("ru") or "").strip()
            mn = (r.get("mn") or "").strip()
            en = (r.get("en") or "").strip()
            image_url = (r.get("image_url") or "").strip()
            example_ru = (r.get("example_ru") or "").strip()

            if level and category and ru:
                rows.append((
                    level,
                    category,
                    ru,
                    mn or None,
                    en or None,
                    image_url or None,
                    example_ru or None,
                ))

    if not rows:
        return 0

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM words")
        count = (await cur.fetchone())[0]

        if count == 0:
            await db.executemany(
                "INSERT INTO words (level, category, ru, mn, en, image_url, example_ru) VALUES (?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            await db.commit()
            return len(rows)

    return 0


async def ensure_user(telegram_id: int, username: str | None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
            (telegram_id, username),
        )
        await db.commit()


async def set_user_ui_lang(telegram_id: int, ui_lang: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET ui_lang=? WHERE telegram_id=?",
            (ui_lang, telegram_id),
        )
        await db.commit()


async def set_user_trans_lang(telegram_id: int, trans_lang: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET trans_lang=? WHERE telegram_id=?",
            (trans_lang, telegram_id),
        )
        await db.commit()


async def set_user_level(telegram_id: int, level: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET level=? WHERE telegram_id=?",
            (level, telegram_id),
        )
        await db.commit()


async def set_user_category(telegram_id: int, category: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET preferred_category=? WHERE telegram_id=?",
            (category, telegram_id),
        )
        await db.commit()


async def get_user_level(telegram_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT level FROM users WHERE telegram_id=?",
            (telegram_id,),
        )
        row = await cur.fetchone()
        return row[0] if row and row[0] else None


async def get_user_category(telegram_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT preferred_category FROM users WHERE telegram_id=?",
            (telegram_id,),
        )
        row = await cur.fetchone()
        return row[0] if row and row[0] else None


async def get_user_trans_lang(telegram_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT trans_lang FROM users WHERE telegram_id=?",
            (telegram_id,),
        )
        row = await cur.fetchone()
        return row[0] if row and row[0] else None


async def get_user_ui_lang(telegram_id: int) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT ui_lang FROM users WHERE telegram_id=?",
            (telegram_id,),
        )
        row = await cur.fetchone()
        return row[0] if row and row[0] else None


async def get_user(telegram_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT telegram_id, username, ui_lang, trans_lang, level, preferred_category, created_at
            FROM users
            WHERE telegram_id=?
            """,
            (telegram_id,),
        )
        row = await cur.fetchone()
        if not row:
            return None

        return {
            "telegram_id": row[0],
            "username": row[1],
            "ui_lang": row[2],
            "trans_lang": row[3],
            "level": row[4],
            "preferred_category": row[5],
            "created_at": row[6],
        }


async def get_next_word_for_user(user_id: int, level: str, category: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR IGNORE INTO user_progress (user_id, level, category, next_word_id)
            VALUES (?, ?, ?, 1)
            """,
            (user_id, level, category),
        )

        cur = await db.execute(
            """
            SELECT next_word_id
            FROM user_progress
            WHERE user_id=? AND level=? AND category=?
            """,
            (user_id, level, category),
        )
        row = await cur.fetchone()
        next_word_id = row[0] if row else 1

        cur = await db.execute(
            """
            SELECT id, ru, mn, en, image_url, example_ru
            FROM words
            WHERE level=? AND category=? AND id >= ?
            ORDER BY id ASC
            LIMIT 1
            """,
            (level, category, next_word_id),
        )
        word = await cur.fetchone()
        if not word:
            return None

        word_id, ru, mn, en, image_url, example_ru = word

        await db.execute(
            """
            UPDATE user_progress
            SET next_word_id=?, updated_at=datetime('now')
            WHERE user_id=? AND level=? AND category=?
            """,
            (word_id + 1, user_id, level, category),
        )
        await db.commit()

        return (ru, mn, en, image_url, example_ru)


async def get_random_word_for_level(level: str, category: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT ru, mn, en, image_url, example_ru
            FROM words
            WHERE level=? AND category=?
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (level, category),
        )
        return await cur.fetchone()


async def get_quiz_options(level: str, category: str, limit: int = 4):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT id, ru, mn, en
            FROM words
            WHERE level=? AND category=?
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (level, category, limit),
        )
        return await cur.fetchall()


def current_week_id() -> str:
    y, w, _ = datetime.date.today().isocalendar()
    return f"{y}-W{w:02d}"


async def add_weekly_score(user_id: int, level: str, score_delta: int) -> None:
    week_id = current_week_id()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO weekly_scores (user_id, level, week_id, score)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, level, week_id) DO UPDATE SET
              score = score + excluded.score
            """,
            (user_id, level, week_id, score_delta),
        )
        await db.commit()
async def get_leaderboard(level: str, limit: int = 10):
    week_id = current_week_id()

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT users.username, weekly_scores.score
            FROM weekly_scores
            JOIN users ON users.telegram_id = weekly_scores.user_id
            WHERE weekly_scores.level=? AND weekly_scores.week_id=?
            ORDER BY weekly_scores.score DESC
            LIMIT ?
            """,
            (level, week_id, limit),
        )
        return await cur.fetchall()
async def get_user_rank(user_id: int, level: str):
    week_id = current_week_id()

    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT user_id, score
            FROM weekly_scores
            WHERE level=? AND week_id=?
            ORDER BY score DESC
            """,
            (level, week_id),
        )

        rows = await cur.fetchall()

        rank = 1
        for uid, score in rows:
            if uid == user_id:
                return rank, score
            rank += 1

    return None, 0
async def get_weak_words(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
        SELECT w.ru, w.mn, w.en
        FROM weak_words ww
        JOIN words w ON w.id = ww.word_id
        WHERE ww.user_id = ?
        ORDER BY ww.wrong_count DESC
        LIMIT 10
        """, (user_id,))
        return await cursor.fetchall()
async def get_quiz_sentence_options(level: str, category: str, limit: int = 4):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT id, ru, mn, en, example_ru
            FROM words
            WHERE level=? AND category=? AND example_ru IS NOT NULL AND example_ru != ''
            ORDER BY RANDOM()
            LIMIT ?
            """,
            (level, category, limit),
        )
        return await cur.fetchall()
async def find_word(query: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT level, category, ru, mn, en, example_ru
            FROM words
            WHERE lower(ru)=lower(?)
               OR lower(mn)=lower(?)
               OR lower(en)=lower(?)
            LIMIT 1
            """,
            (query, query, query),
        )
        return await cur.fetchone()
async def get_weak_quiz_options(user_id: int, limit: int = 4):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT w.id, w.ru, w.mn, w.en
            FROM weak_words ww
            JOIN words w ON w.id = ww.word_id
            WHERE ww.user_id = ?
            ORDER BY ww.wrong_count DESC, RANDOM()
            LIMIT ?
            """,
            (user_id, limit),
        )
        return await cur.fetchall()
async def improve_weak_word(user_id: int, word_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT wrong_count
            FROM weak_words
            WHERE user_id=? AND word_id=?
            """,
            (user_id, word_id),
        )
        row = await cur.fetchone()

        if not row:
            return

        wrong_count = row[0]

        if wrong_count <= 1:
            await db.execute(
                "DELETE FROM weak_words WHERE user_id=? AND word_id=?",
                (user_id, word_id),
            )
        else:
            await db.execute(
                """
                UPDATE weak_words
                SET wrong_count = wrong_count - 1
                WHERE user_id=? AND word_id=?
                """,
                (user_id, word_id),
            )

        await db.commit()
async def find_word_anywhere(word: str):
    async with aiosqlite.connect(DB_PATH) as db:

        cur = await db.execute(
            """
            SELECT ru, mn, en, image_url
            FROM words
            WHERE
                LOWER(ru)=?
                OR LOWER(mn)=?
                OR LOWER(en)=?
            LIMIT 1
            """,
            (word, word, word),
        )

        return await cur.fetchone()
async def seed_grammar():
    topics = [
        (
            "pronouns",
            "👤 Личные местоимения",
            "👤 Хувийн төлөөний үг",
            "👤 Personal pronouns",
            "Личные местоимения указывают на человека или группу людей: я, ты, он, она, мы, вы, они.",
            "Хувийн төлөөний үг нь хүн эсвэл хүмүүсийг заана: я, ты, он, она, мы, вы, они.",
            "Personal pronouns refer to a person or a group of people: я, ты, он, она, мы, вы, они.",
            "Я студент.",
            "Они учатся в университете.",
        ),
        (
            "gender",
            "🔤 Род существительных",
            "🔤 Нэр үгийн хүйс",
            "🔤 Noun gender",
            "В русском языке существительные бывают мужского, женского и среднего рода.",
            "Орос хэлэнд нэр үг эр, эм, саармаг гэсэн 3 хүйстэй.",
            "Russian nouns have three genders: masculine, feminine, and neuter.",
            "Студент — мужской род.",
            "Книга — женский род.",
        ),
        (
            "plural",
            "🔢 Множественное число",
            "🔢 Олон тоо",
            "🔢 Plural form",
            "Множественное число показывает, что предметов больше одного.",
            "Олон тоо нь нэгээс олон зүйл байгааг илэрхийлнэ.",
            "The plural form shows that there is more than one object.",
            "Студент — студенты.",
            "Книга — книги.",
        ),
        (
            "present_tense",
            "⏰ Настоящее время",
            "⏰ Одоогийн цаг",
            "⏰ Present tense",
            "Настоящее время показывает действие, которое происходит сейчас или регулярно.",
            "Одоогийн цаг нь яг одоо эсвэл тогтмол болж буй үйлдлийг илэрхийлнэ.",
            "Present tense describes actions happening now or regularly.",
            "Я читаю книгу.",
            "Он работает каждый день.",
        ),
        (
            "cases",
            "📚 Падежи",
            "📚 Тийн ялгал",
            "📚 Cases",
            "Падеж показывает роль слова в предложении. В русском языке есть шесть падежей.",
            "Тийн ялгал нь өгүүлбэр дэх үгийн үүргийг илэрхийлнэ. Орос хэлэнд 6 тийн ялгал байдаг.",
            "Cases show the role of a word in a sentence. Russian has six cases.",
            "Я читаю книгу.",
            "Мы говорим о проекте.",
        ),
        (
            "past_tense",
            "🕓 Прошедшее время",
            "🕓 Өнгөрсөн цаг",
            "🕓 Past tense",
            "Прошедшее время показывает действие, которое уже произошло.",
            "Өнгөрсөн цаг нь аль хэдийн болсон үйлдлийг илэрхийлнэ.",
            "Past tense describes an action that has already happened.",
            "Я читал книгу вчера.",
            "Она работала в офисе.",
        ),
        (
            "future_tense",
            "🕔 Будущее время",
            "🕔 Ирээдүйн цаг",
            "🕔 Future tense",
            "Будущее время показывает действие, которое произойдёт потом.",
            "Ирээдүйн цаг нь дараа болох үйлдлийг илэрхийлнэ.",
            "Future tense describes an action that will happen later.",
            "Я буду учиться вечером.",
            "Мы поедем в Москву завтра.",
        ),
        (
            "adjectives",
            "📏 Прилагательные",
            "📏 Тэмдэг нэр",
            "📏 Adjectives",
            "Прилагательные описывают предмет и согласуются с существительным по роду и числу.",
            "Тэмдэг нэр нь юмсыг тодорхойлж, нэр үгтэй хүйс ба тоогоороо зохицно.",
            "Adjectives describe nouns and agree with them in gender and number.",
            "Новый дом.",
            "Интересная книга.",
        ),
    ]

    quiz_rows = [
        ("pronouns", "___ студент.", "Я", "Книга", "Они", 1),
        ("gender", "Слово «книга» какого рода?", "мужского", "женского", "среднего", 2),
        ("plural", "Правильная форма множественного числа: студент → ?", "студента", "студенты", "студенту", 2),
        ("present_tense", "Я ___ книгу.", "читаю", "читал", "буду читать", 1),
        ("cases", "Я читаю ___", "книга", "книгу", "книге", 2),
        ("past_tense", "Вчера она ___ в офисе.", "работает", "работала", "будет работать", 2),
        ("future_tense", "Завтра мы ___ в Москву.", "едем вчера", "поедем", "ехали", 2),
        ("adjectives", "Правильно: ___ книга", "интересный", "интересная", "интересное", 2),
    ]

    async with aiosqlite.connect(DB_PATH) as db:
        for row in topics:
            await db.execute(
                """
                INSERT OR IGNORE INTO grammar_topics
                (topic_key, title_ru, title_mn, title_en, theory_ru, theory_mn, theory_en, example1_ru, example2_ru)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )

        for row in quiz_rows:
            await db.execute(
                """
                INSERT OR IGNORE INTO grammar_quiz
                (topic_key, question_ru, option1, option2, option3, correct_option)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                row,
            )

        await db.commit()

async def get_grammar_topics():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT topic_key, title_ru FROM grammar_topics ORDER BY id"
        )
        return await cur.fetchall()


async def get_grammar_topic(topic_key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT
                title_ru, title_mn, title_en,
                theory_ru, theory_mn, theory_en,
                example1_ru, example2_ru
            FROM grammar_topics
            WHERE topic_key = ?
            """,
            (topic_key,),
        )
        return await cur.fetchone()


async def get_grammar_quiz(topic_key: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT id, question_ru, option1, option2, option3, correct_option
            FROM grammar_quiz
            WHERE topic_key=?
            ORDER BY RANDOM()
            LIMIT 1
            """,
            (topic_key,),
        )
        return await cur.fetchone()


async def get_grammar_quiz_answer(quiz_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT correct_option FROM grammar_quiz WHERE id=?",
            (quiz_id,),
        )
        row = await cur.fetchone()
        return row[0] if row else None