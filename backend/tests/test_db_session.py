"""
Tests for SQLAlchemy session factory and lifecycle
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db.base import Base


def test_sqlite_in_memory_session():
    test_engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    
    Base.metadata.create_all(bind=test_engine)
    
    session = TestingSessionLocal()
    try:
        result = session.execute(text("SELECT 1")).scalar()
        assert result == 1
    finally:
        session.close()
