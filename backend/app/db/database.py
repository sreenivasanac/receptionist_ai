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
        
        # V2 Tables
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT,
                email TEXT,
                phone TEXT,
                visit_count INTEGER DEFAULT 0,
                last_visit_date TEXT,
                favorite_service_id TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id),
                FOREIGN KEY (favorite_service_id) REFERENCES services(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                customer_id TEXT,
                service_id TEXT NOT NULL,
                staff_id TEXT,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                customer_email TEXT,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL,
                status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no_show')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (service_id) REFERENCES services(id),
                FOREIGN KEY (staff_id) REFERENCES staff(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                interest TEXT NOT NULL,
                notes TEXT,
                company TEXT,
                status TEXT DEFAULT 'new' CHECK (status IN ('new', 'contacted', 'qualified', 'converted', 'lost')),
                source TEXT DEFAULT 'chatbot',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS waitlist (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                customer_id TEXT,
                service_id TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                customer_contact TEXT NOT NULL,
                preferred_dates TEXT DEFAULT '[]',
                preferred_times TEXT DEFAULT '[]',
                contact_method TEXT DEFAULT 'phone' CHECK (contact_method IN ('phone', 'email', 'sms')),
                status TEXT DEFAULT 'waiting' CHECK (status IN ('waiting', 'notified', 'booked', 'expired', 'cancelled')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (service_id) REFERENCES services(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sms_campaigns (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                name TEXT,
                message TEXT NOT NULL,
                recipient_filter TEXT DEFAULT '{}',
                recipient_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'scheduled', 'sending', 'sent', 'failed')),
                scheduled_at TIMESTAMP,
                sent_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        
        # Create indexes for V2 tables
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_business ON customers(business_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_business ON appointments(business_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_customer ON appointments(customer_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_business ON leads(business_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_waitlist_business ON waitlist(business_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_waitlist_status ON waitlist(status)")
        
        # Unique constraints for data integrity
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_business_phone ON customers(business_id, phone) WHERE phone IS NOT NULL")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_business_email ON customers(business_id, email) WHERE email IS NOT NULL")
        
        # V3 Tables
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                trigger_type TEXT NOT NULL CHECK (trigger_type IN ('keyword', 'segment', 'time')),
                trigger_config TEXT DEFAULT '{}',
                actions TEXT DEFAULT '[]',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unanswered_questions (
                id TEXT PRIMARY KEY,
                business_id TEXT NOT NULL,
                question_text TEXT NOT NULL,
                category TEXT,
                occurrence_count INTEGER DEFAULT 1,
                last_asked_at TIMESTAMP,
                suggested_answer TEXT,
                is_resolved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (business_id) REFERENCES businesses(id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS waitlist_notifications (
                id TEXT PRIMARY KEY,
                waitlist_id TEXT NOT NULL,
                cancelled_appointment_id TEXT,
                notification_sent_at TIMESTAMP,
                response TEXT CHECK (response IN ('accepted', 'declined', 'expired', 'pending')),
                response_at TIMESTAMP,
                booking_created INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (waitlist_id) REFERENCES waitlist(id),
                FOREIGN KEY (cancelled_appointment_id) REFERENCES appointments(id)
            )
        """)
        
        # Create indexes for V3 tables
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_business ON workflows(business_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_workflows_active ON workflows(is_active)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_unanswered_business ON unanswered_questions(business_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_unanswered_resolved ON unanswered_questions(is_resolved)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_waitlist_notifications_waitlist ON waitlist_notifications(waitlist_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_business ON conversations(business_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id)")
        
        conn.commit()
