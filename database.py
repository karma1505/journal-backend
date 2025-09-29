from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

if os.getenv("VERCEL"):
    # Production: Vercel Postgres
    DATABASE_URL = os.getenv("POSTGRES_URL")
else:
    # Development: SQLite
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./journal.db")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)