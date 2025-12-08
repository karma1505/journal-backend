from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Entry(Base):
    __tablename__ = "entries"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    image_path = Column(String(500), nullable=True)
    view_count = Column(Integer, default=0, nullable=False)

class EntryView(Base):
    __tablename__ = "entry_views"
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("entries.id", ondelete="CASCADE"), nullable=False)
    ip_hash = Column(String(64), nullable=False)  # SHA-256 hash
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Composite index for fast duplicate checking
    __table_args__ = (
        Index('idx_entry_ip_time', 'entry_id', 'ip_hash', 'viewed_at'),
    )
