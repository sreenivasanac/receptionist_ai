"""SQLite database connection and utilities."""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from app.config import settings


def get_db_path() -> Path:
    """Get the database file path, creating parent directories if needed."""
    db_path = settings.DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@contextmanager
def get_db_connection():
    """Get a database connection context manager."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                config_yaml TEXT,
                features_enabled TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                role TEXT NOT NULL CHECK (role IN ('admin', 'business_owner')),
                business_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                duration_minutes INTEGER,
                price REAL,
                requires_consultation INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS staff (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                name TEXT NOT NULL,
                role_title TEXT,
                services_offered TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                messages TEXT DEFAULT '[]',
                customer_info TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraped_content (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                url TEXT NOT NULL,
                raw_content TEXT,
                parsed_data TEXT DEFAULT '{}',
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        
        conn.commit()
