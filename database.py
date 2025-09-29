from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

# Use Supabase PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres.sginmhviemnhjorlzbme:aVlfGiw9rLuTmqEs@aws-1-us-east-1.pooler.supabase.com:6543/postgres")

# Debug: Print the database URL (remove this after testing)
print(f"Database URL: {DATABASE_URL}")

try:
    engine = create_async_engine(
        DATABASE_URL, 
        echo=False,  # Disable echo to reduce logs
        pool_pre_ping=True,
        pool_recycle=60,  # Shorter recycle time for serverless
        pool_size=1,
        max_overflow=0,
        pool_timeout=10,  # Shorter timeout
        pool_reset_on_return='rollback',  # More aggressive reset
        connect_args={
            "server_settings": {
                "application_name": "journal_api",
            }
        }
    )
    SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    print("Database engine created successfully")
except Exception as e:
    print(f"Error creating database engine: {e}")
    raise