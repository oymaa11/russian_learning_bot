import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add it to .env or Railway Variables.")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is missing. Add it to .env or Railway Variables.")