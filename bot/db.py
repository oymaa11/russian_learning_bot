import asyncpg
import csv
import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing.")

pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    global pool
    if pool is None:
        pool = await asyncpg.create_pool(DATABASE_URL)
    return pool


async def init_db() -> None:
    db = await get_pool()

    async with db.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username TEXT,
            ui_lang TEXT,
            trans_lang TEXT,
            level TEXT,
            preferred_category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id SERIAL PRIMARY KEY,
            level TEXT NOT NULL,
            category TEXT NOT NULL,
            ru TEXT NOT NULL,
            mn TEXT,
            en TEXT,
            image_url TEXT,
            example_ru TEXT
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS weekly_scores (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            week_id TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            UNIQUE(user_id, level, week_id)
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            id SERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            level TEXT NOT NULL,
            category TEXT NOT NULL,
            next_word_id INTEGER DEFAULT 1,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, level, category)
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            user_id BIGINT PRIMARY KEY,
            words_learned INTEGER DEFAULT 0,
            quizzes_taken INTEGER DEFAULT 0,
            correct_answers INTEGER DEFAULT 0,
            total_score INTEGER DEFAULT 0
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS weak_words (
            user_id BIGINT,
            word_id INTEGER,
            wrong_count INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, word_id)
        );
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS grammar_topics (
            id SERIAL PRIMARY KEY,
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
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS grammar_quiz (
            id SERIAL PRIMARY KEY,
            topic_key TEXT NOT NULL,
            question_ru TEXT NOT NULL,
            option1 TEXT NOT NULL,
            option2 TEXT NOT NULL,
            option3 TEXT NOT NULL,
            correct_option INTEGER NOT NULL
        );
        """)


async def ensure_user_stats(user_id: int) -> None:
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_stats (user_id)
            VALUES ($1)
            ON CONFLICT (user_id) DO NOTHING
            """,
            user_id,
        )


async def increment_words_learned(user_id: int, amount: int = 1) -> None:
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_stats (user_id, words_learned)
            VALUES ($1, $2)
            ON CONFLICT (user_id) DO UPDATE SET
                words_learned = user_stats.words_learned + EXCLUDED.words_learned
            """,
            user_id,
            amount,
        )


async def update_quiz_stats(user_id: int, correct: int, score: int) -> None:
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_stats (user_id, quizzes_taken, correct_answers, total_score)
            VALUES ($1, 1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                quizzes_taken = user_stats.quizzes_taken + 1,
                correct_answers = user_stats.correct_answers + EXCLUDED.correct_answers,
                total_score = user_stats.total_score + EXCLUDED.total_score
            """,
            user_id,
            correct,
            score,
        )


async def get_user_stats(user_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT words_learned, quizzes_taken, correct_answers, total_score
            FROM user_stats
            WHERE user_id = $1
            """,
            user_id,
        )
        if not row:
            return (0, 0, 0, 0)
        return tuple(row)


async def add_weak_word(user_id: int, word_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO weak_words (user_id, word_id, wrong_count)
            VALUES ($1, $2, 1)
            ON CONFLICT (user_id, word_id)
            DO UPDATE SET wrong_count = weak_words.wrong_count + 1
            """,
            user_id,
            word_id,
        )


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

    db = await get_pool()
    async with db.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM words")

        if count == 0:
            await conn.executemany(
                """
                INSERT INTO words (level, category, ru, mn, en, image_url, example_ru)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                rows,
            )
            return len(rows)

    return 0


async def ensure_user(telegram_id: int, username: str | None) -> None:
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_id, username)
            VALUES ($1, $2)
            ON CONFLICT (telegram_id) DO NOTHING
            """,
            telegram_id,
            username,
        )


async def set_user_ui_lang(telegram_id: int, ui_lang: str) -> None:
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE users SET ui_lang = $1 WHERE telegram_id = $2",
            ui_lang,
            telegram_id,
        )


async def set_user_trans_lang(telegram_id: int, trans_lang: str) -> None:
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE users SET trans_lang = $1 WHERE telegram_id = $2",
            trans_lang,
            telegram_id,
        )


async def set_user_level(telegram_id: int, level: str) -> None:
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE users SET level = $1 WHERE telegram_id = $2",
            level,
            telegram_id,
        )


async def set_user_category(telegram_id: int, category: str) -> None:
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            "UPDATE users SET preferred_category = $1 WHERE telegram_id = $2",
            category,
            telegram_id,
        )


async def get_user_level(telegram_id: int) -> str | None:
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval(
            "SELECT level FROM users WHERE telegram_id = $1",
            telegram_id,
        )


async def get_user_category(telegram_id: int) -> str | None:
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval(
            "SELECT preferred_category FROM users WHERE telegram_id = $1",
            telegram_id,
        )


async def get_user_trans_lang(telegram_id: int) -> str | None:
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval(
            "SELECT trans_lang FROM users WHERE telegram_id = $1",
            telegram_id,
        )


async def get_user_ui_lang(telegram_id: int) -> str | None:
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval(
            "SELECT ui_lang FROM users WHERE telegram_id = $1",
            telegram_id,
        )


async def get_user(telegram_id: int) -> dict | None:
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT telegram_id, username, ui_lang, trans_lang, level, preferred_category, created_at
            FROM users
            WHERE telegram_id = $1
            """,
            telegram_id,
        )
        if not row:
            return None
        return dict(row)


async def get_next_word_for_user(user_id: int, level: str, category: str):
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_progress (user_id, level, category, next_word_id)
            VALUES ($1, $2, $3, 1)
            ON CONFLICT (user_id, level, category) DO NOTHING
            """,
            user_id,
            level,
            category,
        )

        next_word_id = await conn.fetchval(
            """
            SELECT next_word_id
            FROM user_progress
            WHERE user_id = $1 AND level = $2 AND category = $3
            """,
            user_id,
            level,
            category,
        )
        next_word_id = next_word_id or 1

        word = await conn.fetchrow(
            """
            SELECT id, ru, mn, en, image_url, example_ru
            FROM words
            WHERE level = $1 AND category = $2 AND id >= $3
            ORDER BY id ASC
            LIMIT 1
            """,
            level,
            category,
            next_word_id,
        )

        if not word:
            return None

        word_id, ru, mn, en, image_url, example_ru = word

        await conn.execute(
            """
            UPDATE user_progress
            SET next_word_id = $1, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = $2 AND level = $3 AND category = $4
            """,
            word_id + 1,
            user_id,
            level,
            category,
        )

        return (ru, mn, en, image_url, example_ru)


async def get_random_word_for_level(level: str, category: str):
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT ru, mn, en, image_url, example_ru
            FROM words
            WHERE level = $1 AND category = $2
            ORDER BY RANDOM()
            LIMIT 1
            """,
            level,
            category,
        )
        return tuple(row) if row else None


async def get_quiz_options(level: str, category: str, limit: int = 4):
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, ru, mn, en
            FROM words
            WHERE level = $1 AND category = $2
            ORDER BY RANDOM()
            LIMIT $3
            """,
            level,
            category,
            limit,
        )
        return [tuple(row) for row in rows]


def current_week_id() -> str:
    y, w, _ = datetime.date.today().isocalendar()
    return f"{y}-W{w:02d}"


async def add_weekly_score(user_id: int, level: str, score_delta: int) -> None:
    week_id = current_week_id()
    db = await get_pool()
    async with db.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO weekly_scores (user_id, level, week_id, score)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, level, week_id) DO UPDATE SET
                score = weekly_scores.score + EXCLUDED.score
            """,
            user_id,
            level,
            week_id,
            score_delta,
        )


async def get_leaderboard(level: str, limit: int = 10):
    week_id = current_week_id()
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT users.username, weekly_scores.score
            FROM weekly_scores
            JOIN users ON users.telegram_id = weekly_scores.user_id
            WHERE weekly_scores.level = $1 AND weekly_scores.week_id = $2
            ORDER BY weekly_scores.score DESC
            LIMIT $3
            """,
            level,
            week_id,
            limit,
        )
        return [tuple(row) for row in rows]


async def get_user_rank(user_id: int, level: str):
    week_id = current_week_id()
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT user_id, score
            FROM weekly_scores
            WHERE level = $1 AND week_id = $2
            ORDER BY score DESC
            """,
            level,
            week_id,
        )

        rank = 1
        for row in rows:
            uid, score = row
            if uid == user_id:
                return rank, score
            rank += 1

    return None, 0


async def get_weak_words(user_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT w.ru, w.mn, w.en
            FROM weak_words ww
            JOIN words w ON w.id = ww.word_id
            WHERE ww.user_id = $1
            ORDER BY ww.wrong_count DESC
            LIMIT 10
            """,
            user_id,
        )
        return [tuple(row) for row in rows]


async def get_quiz_sentence_options(level: str, category: str, limit: int = 4):
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, ru, mn, en, example_ru
            FROM words
            WHERE level = $1 AND category = $2
              AND example_ru IS NOT NULL
              AND example_ru != ''
            ORDER BY RANDOM()
            LIMIT $3
            """,
            level,
            category,
            limit,
        )
        return [tuple(row) for row in rows]


async def find_word(query: str):
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT level, category, ru, mn, en, example_ru
            FROM words
            WHERE LOWER(ru) = LOWER($1)
               OR LOWER(mn) = LOWER($1)
               OR LOWER(en) = LOWER($1)
            LIMIT 1
            """,
            query,
        )
        return tuple(row) if row else None


async def get_weak_quiz_options(user_id: int, limit: int = 4):
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT w.id, w.ru, w.mn, w.en
            FROM weak_words ww
            JOIN words w ON w.id = ww.word_id
            WHERE ww.user_id = $1
            ORDER BY ww.wrong_count DESC, RANDOM()
            LIMIT $2
            """,
            user_id,
            limit,
        )
        return [tuple(row) for row in rows]


async def improve_weak_word(user_id: int, word_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        wrong_count = await conn.fetchval(
            """
            SELECT wrong_count
            FROM weak_words
            WHERE user_id = $1 AND word_id = $2
            """,
            user_id,
            word_id,
        )

        if wrong_count is None:
            return

        if wrong_count <= 1:
            await conn.execute(
                "DELETE FROM weak_words WHERE user_id = $1 AND word_id = $2",
                user_id,
                word_id,
            )
        else:
            await conn.execute(
                """
                UPDATE weak_words
                SET wrong_count = wrong_count - 1
                WHERE user_id = $1 AND word_id = $2
                """,
                user_id,
                word_id,
            )


async def find_word_anywhere(word: str):
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT ru, mn, en, image_url
            FROM words
            WHERE LOWER(ru) = LOWER($1)
               OR LOWER(mn) = LOWER($1)
               OR LOWER(en) = LOWER($1)
            LIMIT 1
            """,
            word,
        )
        return tuple(row) if row else None


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

    db = await get_pool()
    async with db.acquire() as conn:
        for row in topics:
            await conn.execute(
                """
                INSERT INTO grammar_topics
                (topic_key, title_ru, title_mn, title_en, theory_ru, theory_mn, theory_en, example1_ru, example2_ru)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (topic_key) DO NOTHING
                """,
                *row,
            )

        for row in quiz_rows:
            await conn.execute(
                """
                INSERT INTO grammar_quiz
                (topic_key, question_ru, option1, option2, option3, correct_option)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                *row,
            )


async def get_grammar_topics():
    db = await get_pool()
    async with db.acquire() as conn:
        rows = await conn.fetch(
            "SELECT topic_key, title_ru FROM grammar_topics ORDER BY id"
        )
        return [tuple(row) for row in rows]


async def get_grammar_topic(topic_key: str):
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                title_ru, title_mn, title_en,
                theory_ru, theory_mn, theory_en,
                example1_ru, example2_ru
            FROM grammar_topics
            WHERE topic_key = $1
            """,
            topic_key,
        )
        return tuple(row) if row else None


async def get_grammar_quiz(topic_key: str):
    db = await get_pool()
    async with db.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, question_ru, option1, option2, option3, correct_option
            FROM grammar_quiz
            WHERE topic_key = $1
            ORDER BY RANDOM()
            LIMIT 1
            """,
            topic_key,
        )
        return tuple(row) if row else None


async def get_grammar_quiz_answer(quiz_id: int):
    db = await get_pool()
    async with db.acquire() as conn:
        return await conn.fetchval(
            "SELECT correct_option FROM grammar_quiz WHERE id = $1",
            quiz_id,
        )