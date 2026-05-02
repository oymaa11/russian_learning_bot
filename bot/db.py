import csv
from pathlib import Path
from typing import Optional

import asyncpg
from bot.config import DATABASE_URL

# ──────────────────────────────────────────────
#  Глобал pool — нэг удаа үүсгэж бүгдэд ашиглана
# ──────────────────────────────────────────────
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None or _pool._closed:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool and not _pool._closed:
        await _pool.close()
        _pool = None


# ──────────────────────────────────────────────
#  Хүснэгт үүсгэх
# ──────────────────────────────────────────────
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    telegram_id  BIGINT PRIMARY KEY,
    username     TEXT,
    ui_lang      TEXT DEFAULT 'ru',
    trans_lang   TEXT DEFAULT 'mn',
    category     TEXT DEFAULT 'general',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS words (
    id          SERIAL PRIMARY KEY,
    category    TEXT NOT NULL,
    ru          TEXT NOT NULL,
    mn          TEXT,
    en          TEXT,
    image_url   TEXT,
    example_ru  TEXT
);

CREATE TABLE IF NOT EXISTS user_progress (
    telegram_id  BIGINT NOT NULL,
    category     TEXT NOT NULL,
    next_word_id INTEGER DEFAULT 1,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, category)
);
"""


async def init_db() -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLES_SQL)


# ──────────────────────────────────────────────
#  Хэрэглэгч
# ──────────────────────────────────────────────
async def ensure_user(telegram_id: int, username: Optional[str]) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (telegram_id, username)
            VALUES ($1, $2)
            ON CONFLICT (telegram_id) DO NOTHING
            """,
            telegram_id, username,
        )


async def get_user_settings(telegram_id: int) -> dict:
    """ui_lang, trans_lang, category — нэг query-д авна."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT ui_lang, trans_lang, category FROM users WHERE telegram_id=$1",
            telegram_id,
        )
    if row:
        return {
            "ui_lang":    row["ui_lang"]    or "ru",
            "trans_lang": row["trans_lang"] or "mn",
            "category":   row["category"]   or "general",
        }
    return {"ui_lang": "ru", "trans_lang": "mn", "category": "general"}


async def get_ui_lang(telegram_id: int) -> str:
    s = await get_user_settings(telegram_id)
    return s["ui_lang"]
async def get_trans_lang(telegram_id: int) -> str:
    s = await get_user_settings(telegram_id)
    return s["trans_lang"]


async def get_category(telegram_id: int) -> str:
    s = await get_user_settings(telegram_id)
    return s["category"]


async def set_ui_lang(telegram_id: int, ui_lang: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET ui_lang=$1 WHERE telegram_id=$2",
            ui_lang, telegram_id,
        )


async def set_trans_lang(telegram_id: int, trans_lang: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET trans_lang=$1 WHERE telegram_id=$2",
            trans_lang, telegram_id,
        )


async def set_category(telegram_id: int, category: str) -> None:
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET category=$1 WHERE telegram_id=$2",
            category, telegram_id,
        )


# ──────────────────────────────────────────────
#  Үгс — CSV импорт
# ──────────────────────────────────────────────
async def import_words_from_csv(csv_path: str = "words.csv") -> int:
    path = Path(csv_path)
    if not path.exists():
        return 0

    rows = []
    with path.open("r", encoding="utf-8") as f:
        for item in csv.DictReader(f):
            category  = (item.get("category")   or "").strip()
            ru        = (item.get("ru")          or "").strip()
            mn        = (item.get("mn")          or "").strip() or None
            en        = (item.get("en")          or "").strip() or None
            image_url = (item.get("image_url")   or "").strip() or None
            example   = (item.get("example_ru")  or "").strip() or None
            if category and ru:
                rows.append((category, ru, mn, en, image_url, example))

    if not rows:
        return 0

    pool = await get_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM words")
        if count > 0:
            return 0
        await conn.executemany(
            """
            INSERT INTO words (category, ru, mn, en, image_url, example_ru)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            rows,
        )
    return len(rows)


# ──────────────────────────────────────────────
#  Үг авах
# ──────────────────────────────────────────────
async def get_next_word_for_user(telegram_id: int, category: str):
    """Хэрэглэгчийн дарааллын дагуу дараагийн үг буцаана. Эцэст хүрвэл эхнээс эхлэнэ."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO user_progress (telegram_id, category, next_word_id)
            VALUES ($1, $2, 1)
            ON CONFLICT (telegram_id, category) DO NOTHING
            """,
            telegram_id, category,
        )
        next_id = await conn.fetchval(
            "SELECT next_word_id FROM user_progress WHERE telegram_id=$1 AND category=$2",
            telegram_id, category,
        )
        row = await conn.fetchrow(
            """
            SELECT id, category, ru, mn, en, image_url, example_ru
            FROM words
            WHERE category=$1 AND id >= $2
            ORDER BY id ASC LIMIT 1
            """,
            category, next_id,
        )
        if not row:
            row = await conn.fetchrow(
                """
                SELECT id, category, ru, mn, en, image_url, example_ru
                FROM words WHERE category=$1 ORDER BY id ASC LIMIT 1
                """,
                category,
            )
        if row:
            await conn.execute(
                """
                UPDATE user_progress
                SET next_word_id=$1, updated_at=CURRENT_TIMESTAMP
                WHERE telegram_id=$2 AND category=$3
                """,
                row["id"] + 1, telegram_id, category,
            )
    return row


async def find_word(query: str):
    """Хэрэглэгчийн бичсэн үгийг ru/mn/en-д хайна."""
    query = query.strip()
    if not query:
        return None
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT id, category, ru, mn, en, image_url, example_ru
            FROM words
            WHERE LOWER(ru)=LOWER($1)
               OR LOWER(mn)=LOWER($1)
               OR LOWER(en)=LOWER($1)
            LIMIT 1
            """,
            query,
        )


async def get_quiz_options(category: str, limit: int = 4):
    """Quiz-д санамсаргүй үгс буцаана."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetch(
            """
            SELECT id, ru, mn, en
            FROM words
            WHERE category=$1
            ORDER BY RANDOM()
            LIMIT $2
            """,
            category, limit,
        )