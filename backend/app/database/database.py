import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# If no URL is provided, or if it points to localhost (which won't work on Render), fallback to SQLite
if not DATABASE_URL or "localhost" in DATABASE_URL:
    DATABASE_URL = "sqlite:///./chatbot.db"

# SQLite requires specific connect_args to avoid thread issues
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()