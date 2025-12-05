"""Analytics repository for V3 dashboard metrics."""
import json
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field

from app.db.database import get_db_connection


class DateRange(BaseModel):
    """Date range for analytics queries."""
    start_date: str
    end_date: str


class AnalyticsSummary(BaseModel):
    """Summary analytics for dashboard."""
    total_leads: int = 0
    total_appointments: int = 0
    total_conversations: int = 0
    total_customers: int = 0
    conversion_rate: float = 0.0
    leads_this_period: int = 0
    appointments_this_period: int = 0
    conversations_this_period: int = 0


class LeadStats(BaseModel):
    """Lead statistics."""
    total: int = 0
    by_status: dict = Field(default_factory=dict)
    by_source: dict = Field(default_factory=dict)
    by_day: list[dict] = Field(default_factory=list)
    conversion_rate: float = 0.0


class AppointmentStats(BaseModel):
    """Appointment statistics."""
    total: int = 0
    by_status: dict = Field(default_factory=dict)
    by_service: list[dict] = Field(default_factory=list)
    by_day: list[dict] = Field(default_factory=list)
    completion_rate: float = 0.0


class ConversationStats(BaseModel):
    """Conversation statistics."""
    total: int = 0
    avg_message_count: float = 0.0
    by_day: list[dict] = Field(default_factory=list)
    peak_hours: list[dict] = Field(default_factory=list)


def get_date_range(period: str) -> DateRange:
    """Get date range for a period."""
    today = datetime.now().date()
    
    if period == "today":
        return DateRange(start_date=str(today), end_date=str(today))
    elif period == "yesterday":
        yesterday = today - timedelta(days=1)
        return DateRange(start_date=str(yesterday), end_date=str(yesterday))
    elif period == "this_week":
        start = today - timedelta(days=today.weekday())
        return DateRange(start_date=str(start), end_date=str(today))
    elif period == "last_week":
        end = today - timedelta(days=today.weekday() + 1)
        start = end - timedelta(days=6)
        return DateRange(start_date=str(start), end_date=str(end))
    elif period == "this_month":
        start = today.replace(day=1)
        return DateRange(start_date=str(start), end_date=str(today))
    elif period == "last_month":
        first_of_month = today.replace(day=1)
        end = first_of_month - timedelta(days=1)
        start = end.replace(day=1)
        return DateRange(start_date=str(start), end_date=str(end))
    elif period == "last_30_days":
        start = today - timedelta(days=30)
        return DateRange(start_date=str(start), end_date=str(today))
    elif period == "last_90_days":
        start = today - timedelta(days=90)
        return DateRange(start_date=str(start), end_date=str(today))
    else:
        start = today - timedelta(days=30)
        return DateRange(start_date=str(start), end_date=str(today))


class AnalyticsRepository:
    """Repository for analytics queries."""
    
    def get_summary(
        self,
        business_id: str,
        period: str = "last_30_days"
    ) -> AnalyticsSummary:
        """Get summary analytics for dashboard."""
        date_range = get_date_range(period)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM leads WHERE business_id = ?",
                (business_id,)
            )
            total_leads = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM appointments WHERE business_id = ?",
                (business_id,)
            )
            total_appointments = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM conversations WHERE business_id = ?",
                (business_id,)
            )
            total_conversations = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM customers WHERE business_id = ?",
                (business_id,)
            )
            total_customers = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM leads WHERE business_id = ? AND date(created_at) BETWEEN ? AND ?",
                (business_id, date_range.start_date, date_range.end_date)
            )
            leads_period = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM appointments WHERE business_id = ? AND date BETWEEN ? AND ?",
                (business_id, date_range.start_date, date_range.end_date)
            )
            appointments_period = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM conversations WHERE business_id = ? AND date(created_at) BETWEEN ? AND ?",
                (business_id, date_range.start_date, date_range.end_date)
            )
            conversations_period = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM leads WHERE business_id = ? AND status = 'converted'",
                (business_id,)
            )
            converted_leads = cursor.fetchone()["count"]
            conversion_rate = (converted_leads / total_leads * 100) if total_leads > 0 else 0.0
            
            return AnalyticsSummary(
                total_leads=total_leads,
                total_appointments=total_appointments,
                total_conversations=total_conversations,
                total_customers=total_customers,
                conversion_rate=round(conversion_rate, 1),
                leads_this_period=leads_period,
                appointments_this_period=appointments_period,
                conversations_this_period=conversations_period
            )
    
    def get_lead_stats(
        self,
        business_id: str,
        period: str = "last_30_days"
    ) -> LeadStats:
        """Get detailed lead statistics."""
        date_range = get_date_range(period)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM leads WHERE business_id = ? AND date(created_at) BETWEEN ? AND ?",
                (business_id, date_range.start_date, date_range.end_date)
            )
            total = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT status, COUNT(*) as count FROM leads WHERE business_id = ? AND date(created_at) BETWEEN ? AND ? GROUP BY status",
                (business_id, date_range.start_date, date_range.end_date)
            )
            by_status = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            cursor.execute(
                "SELECT source, COUNT(*) as count FROM leads WHERE business_id = ? AND date(created_at) BETWEEN ? AND ? GROUP BY source",
                (business_id, date_range.start_date, date_range.end_date)
            )
            by_source = {row["source"]: row["count"] for row in cursor.fetchall()}
            
            cursor.execute(
                "SELECT date(created_at) as date, COUNT(*) as count FROM leads WHERE business_id = ? AND date(created_at) BETWEEN ? AND ? GROUP BY date(created_at) ORDER BY date",
                (business_id, date_range.start_date, date_range.end_date)
            )
            by_day = [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]
            
            converted = by_status.get("converted", 0)
            conversion_rate = (converted / total * 100) if total > 0 else 0.0
            
            return LeadStats(
                total=total,
                by_status=by_status,
                by_source=by_source,
                by_day=by_day,
                conversion_rate=round(conversion_rate, 1)
            )
    
    def get_appointment_stats(
        self,
        business_id: str,
        period: str = "last_30_days"
    ) -> AppointmentStats:
        """Get detailed appointment statistics."""
        date_range = get_date_range(period)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM appointments WHERE business_id = ? AND date BETWEEN ? AND ?",
                (business_id, date_range.start_date, date_range.end_date)
            )
            total = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT status, COUNT(*) as count FROM appointments WHERE business_id = ? AND date BETWEEN ? AND ? GROUP BY status",
                (business_id, date_range.start_date, date_range.end_date)
            )
            by_status = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            cursor.execute("""
                SELECT s.name as service_name, COUNT(*) as count 
                FROM appointments a 
                LEFT JOIN services s ON a.service_id = s.id 
                WHERE a.business_id = ? AND a.date BETWEEN ? AND ? 
                GROUP BY a.service_id 
                ORDER BY count DESC 
                LIMIT 10
            """, (business_id, date_range.start_date, date_range.end_date))
            by_service = [{"service": row["service_name"] or "Unknown", "count": row["count"]} for row in cursor.fetchall()]
            
            cursor.execute(
                "SELECT date, COUNT(*) as count FROM appointments WHERE business_id = ? AND date BETWEEN ? AND ? GROUP BY date ORDER BY date",
                (business_id, date_range.start_date, date_range.end_date)
            )
            by_day = [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]
            
            completed = by_status.get("completed", 0)
            completion_rate = (completed / total * 100) if total > 0 else 0.0
            
            return AppointmentStats(
                total=total,
                by_status=by_status,
                by_service=by_service,
                by_day=by_day,
                completion_rate=round(completion_rate, 1)
            )
    
    def get_conversation_stats(
        self,
        business_id: str,
        period: str = "last_30_days"
    ) -> ConversationStats:
        """Get detailed conversation statistics."""
        date_range = get_date_range(period)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM conversations WHERE business_id = ? AND date(created_at) BETWEEN ? AND ?",
                (business_id, date_range.start_date, date_range.end_date)
            )
            total = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT messages FROM conversations WHERE business_id = ? AND date(created_at) BETWEEN ? AND ?",
                (business_id, date_range.start_date, date_range.end_date)
            )
            rows = cursor.fetchall()
            total_messages = 0
            for row in rows:
                messages = json.loads(row["messages"] or "[]")
                total_messages += len(messages)
            avg_message_count = (total_messages / total) if total > 0 else 0.0
            
            cursor.execute(
                "SELECT date(created_at) as date, COUNT(*) as count FROM conversations WHERE business_id = ? AND date(created_at) BETWEEN ? AND ? GROUP BY date(created_at) ORDER BY date",
                (business_id, date_range.start_date, date_range.end_date)
            )
            by_day = [{"date": row["date"], "count": row["count"]} for row in cursor.fetchall()]
            
            cursor.execute(
                "SELECT strftime('%H', created_at) as hour, COUNT(*) as count FROM conversations WHERE business_id = ? AND date(created_at) BETWEEN ? AND ? GROUP BY hour ORDER BY count DESC LIMIT 5",
                (business_id, date_range.start_date, date_range.end_date)
            )
            peak_hours = [{"hour": f"{row['hour']}:00", "count": row["count"]} for row in cursor.fetchall()]
            
            return ConversationStats(
                total=total,
                avg_message_count=round(avg_message_count, 1),
                by_day=by_day,
                peak_hours=peak_hours
            )
    
    def get_waitlist_stats(
        self,
        business_id: str,
        period: str = "last_30_days"
    ) -> dict:
        """Get waitlist conversion statistics."""
        date_range = get_date_range(period)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT COUNT(*) as count FROM waitlist WHERE business_id = ? AND date(created_at) BETWEEN ? AND ?",
                (business_id, date_range.start_date, date_range.end_date)
            )
            total = cursor.fetchone()["count"]
            
            cursor.execute(
                "SELECT status, COUNT(*) as count FROM waitlist WHERE business_id = ? AND date(created_at) BETWEEN ? AND ? GROUP BY status",
                (business_id, date_range.start_date, date_range.end_date)
            )
            by_status = {row["status"]: row["count"] for row in cursor.fetchall()}
            
            booked = by_status.get("booked", 0)
            conversion_rate = (booked / total * 100) if total > 0 else 0.0
            
            return {
                "total": total,
                "by_status": by_status,
                "conversion_rate": round(conversion_rate, 1),
                "booked": booked,
                "waiting": by_status.get("waiting", 0),
                "notified": by_status.get("notified", 0)
            }


analytics_repo = AnalyticsRepository()
