"""Customers repository for data access."""
from typing import Optional

from app.db.database import get_db_connection
from app.repositories.base import BaseRepository
from app.models.customer import Customer, CustomerCreate, CustomerUpdate


class CustomerRepository(BaseRepository[Customer]):
    """Repository for customer data access."""
    
    table_name = "customers"
    
    def _row_to_model(self, row, favorite_service_name: Optional[str] = None) -> Customer:
        """Convert a database row to a Customer model."""
        service_name = favorite_service_name
        if service_name is None:
            try:
                service_name = row["favorite_service_name"]
            except (IndexError, KeyError):
                service_name = None
        return Customer(
            id=row["id"],
            business_id=row["business_id"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            email=row["email"],
            phone=row["phone"],
            visit_count=row["visit_count"],
            last_visit_date=row["last_visit_date"],
            favorite_service_id=row["favorite_service_id"],
            favorite_service_name=service_name,
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )
    
    def find_by_business(
        self,
        business_id: str,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Customer]:
        """Find customers for a business with optional search."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT c.*, s.name as favorite_service_name
                FROM customers c
                LEFT JOIN services s ON c.favorite_service_id = s.id
                WHERE c.business_id = ?
            """
            params = [business_id]
            
            if search:
                query += """ AND (
                    c.first_name LIKE ? OR 
                    c.last_name LIKE ? OR 
                    c.email LIKE ? OR 
                    c.phone LIKE ?
                )"""
                search_param = f"%{search}%"
                params.extend([search_param] * 4)
            
            query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            return [self._row_to_model(row) for row in cursor.fetchall()]
    
    def find_by_phone(self, business_id: str, phone: str) -> Optional[Customer]:
        """Find a customer by phone number."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, s.name as favorite_service_name
                FROM customers c
                LEFT JOIN services s ON c.favorite_service_id = s.id
                WHERE c.business_id = ? AND c.phone = ?
            """, (business_id, phone))
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def find_by_email(self, business_id: str, email: str) -> Optional[Customer]:
        """Find a customer by email."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, s.name as favorite_service_name
                FROM customers c
                LEFT JOIN services s ON c.favorite_service_id = s.id
                WHERE c.business_id = ? AND c.email = ?
            """, (business_id, email))
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def find_by_phone_or_email(
        self,
        business_id: str,
        phone: Optional[str] = None,
        email: Optional[str] = None
    ) -> Optional[Customer]:
        """Find a customer by phone or email."""
        if not phone and not email:
            return None
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT c.*, s.name as favorite_service_name
                FROM customers c
                LEFT JOIN services s ON c.favorite_service_id = s.id
                WHERE c.business_id = ?
            """
            params = [business_id]
            
            if phone and email:
                query += " AND (c.phone = ? OR c.email = ?)"
                params.extend([phone, email])
            elif phone:
                query += " AND c.phone = ?"
                params.append(phone)
            else:
                query += " AND c.email = ?"
                params.append(email)
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def find_with_service_name(self, business_id: str, customer_id: str) -> Optional[Customer]:
        """Find a customer with their favorite service name."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT c.*, s.name as favorite_service_name
                FROM customers c
                LEFT JOIN services s ON c.favorite_service_id = s.id
                WHERE c.id = ? AND c.business_id = ?
            """, (customer_id, business_id))
            row = cursor.fetchone()
            return self._row_to_model(row) if row else None
    
    def create(self, business_id: str, data: CustomerCreate) -> Customer:
        """Create a new customer."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            customer_id = self._generate_id()
            now = self._now()
            
            cursor.execute("""
                INSERT INTO customers 
                (id, business_id, first_name, last_name, email, phone, notes, visit_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """, (
                customer_id,
                business_id,
                data.first_name,
                data.last_name,
                data.email,
                data.phone,
                data.notes,
                now,
                now
            ))
            conn.commit()
            
            return self.find_with_service_name(business_id, customer_id)
    
    def create_simple(
        self,
        business_id: str,
        first_name: str,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Create a new customer and return the ID."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            customer_id = self._generate_id()
            now = self._now()
            
            cursor.execute("""
                INSERT INTO customers 
                (id, business_id, first_name, last_name, email, phone, notes, visit_count, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
            """, (
                customer_id,
                business_id,
                first_name,
                last_name,
                email,
                phone,
                notes,
                now,
                now
            ))
            conn.commit()
            
            return customer_id
    
    def update(self, business_id: str, customer_id: str, data: CustomerUpdate) -> Optional[Customer]:
        """Update a customer."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if data.first_name is not None:
                updates.append("first_name = ?")
                params.append(data.first_name)
            if data.last_name is not None:
                updates.append("last_name = ?")
                params.append(data.last_name)
            if data.email is not None:
                updates.append("email = ?")
                params.append(data.email)
            if data.phone is not None:
                updates.append("phone = ?")
                params.append(data.phone)
            if data.notes is not None:
                updates.append("notes = ?")
                params.append(data.notes)
            
            if not updates:
                return self.find_with_service_name(business_id, customer_id)
            
            updates.append("updated_at = ?")
            params.append(self._now())
            params.extend([customer_id, business_id])
            
            cursor.execute(f"""
                UPDATE customers SET {', '.join(updates)}
                WHERE id = ? AND business_id = ?
            """, params)
            conn.commit()
            
            if cursor.rowcount == 0:
                return None
            
            return self.find_with_service_name(business_id, customer_id)
    
    def update_visit(
        self,
        customer_id: str,
        visit_date: str,
        service_id: Optional[str] = None
    ):
        """Update customer visit count and last visit date."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = self._now()
            
            if service_id:
                cursor.execute("""
                    UPDATE customers 
                    SET visit_count = visit_count + 1, 
                        last_visit_date = ?,
                        favorite_service_id = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (visit_date, service_id, now, customer_id))
            else:
                cursor.execute("""
                    UPDATE customers 
                    SET visit_count = visit_count + 1, 
                        last_visit_date = ?,
                        updated_at = ?
                    WHERE id = ?
                """, (visit_date, now, customer_id))
            
            conn.commit()
    
    def email_exists(self, business_id: str, email: str, exclude_id: Optional[str] = None) -> bool:
        """Check if email already exists for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if exclude_id:
                cursor.execute(
                    "SELECT 1 FROM customers WHERE business_id = ? AND email = ? AND id != ?",
                    (business_id, email, exclude_id)
                )
            else:
                cursor.execute(
                    "SELECT 1 FROM customers WHERE business_id = ? AND email = ?",
                    (business_id, email)
                )
            return cursor.fetchone() is not None
    
    def phone_exists(self, business_id: str, phone: str, exclude_id: Optional[str] = None) -> bool:
        """Check if phone already exists for a business."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if exclude_id:
                cursor.execute(
                    "SELECT 1 FROM customers WHERE business_id = ? AND phone = ? AND id != ?",
                    (business_id, phone, exclude_id)
                )
            else:
                cursor.execute(
                    "SELECT 1 FROM customers WHERE business_id = ? AND phone = ?",
                    (business_id, phone)
                )
            return cursor.fetchone() is not None
    
    def upsert_from_csv(
        self,
        business_id: str,
        first_name: str,
        last_name: Optional[str],
        email: Optional[str],
        phone: Optional[str]
    ) -> bool:
        """Insert or update a customer from CSV import. Returns True if imported."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = self._now()
            
            existing = None
            if email:
                cursor.execute(
                    "SELECT id FROM customers WHERE business_id = ? AND email = ?",
                    (business_id, email)
                )
                existing = cursor.fetchone()
            
            if not existing and phone:
                cursor.execute(
                    "SELECT id FROM customers WHERE business_id = ? AND phone = ?",
                    (business_id, phone)
                )
                existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE customers SET 
                        first_name = ?, last_name = COALESCE(?, last_name),
                        email = COALESCE(?, email), phone = COALESCE(?, phone),
                        updated_at = ?
                    WHERE id = ?
                """, (first_name, last_name, email, phone, now, existing['id']))
            else:
                customer_id = self._generate_id()
                cursor.execute("""
                    INSERT INTO customers 
                    (id, business_id, first_name, last_name, email, phone, visit_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)
                """, (customer_id, business_id, first_name, last_name, email, phone, now, now))
            
            conn.commit()
            return True
    
    def get_with_phone(self, business_id: str, recipient_filter: dict) -> list[dict]:
        """Get customers with phone numbers based on filter."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query, params = self._build_recipient_query(business_id, recipient_filter)
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def count_with_phone(self, business_id: str, recipient_filter: dict) -> int:
        """Count customers with phone numbers based on filter."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            query, params = self._build_recipient_query(business_id, recipient_filter)
            count_query = query.replace("SELECT *", "SELECT COUNT(*) as count")
            cursor.execute(count_query, params)
            return cursor.fetchone()["count"]
    
    def _build_recipient_query(self, business_id: str, filter_data: dict) -> tuple[str, list]:
        """Build SQL query for recipient filtering."""
        query = "SELECT * FROM customers WHERE business_id = ? AND phone IS NOT NULL"
        params = [business_id]
        
        if filter_data.get("custom_ids"):
            placeholders = ",".join(["?" for _ in filter_data["custom_ids"]])
            query += f" AND id IN ({placeholders})"
            params.extend(filter_data["custom_ids"])
        elif not filter_data.get("all_customers"):
            if filter_data.get("visit_count_min"):
                query += " AND visit_count >= ?"
                params.append(filter_data["visit_count_min"])
            if filter_data.get("visit_count_max"):
                query += " AND visit_count <= ?"
                params.append(filter_data["visit_count_max"])
            if filter_data.get("favorite_service_id"):
                query += " AND favorite_service_id = ?"
                params.append(filter_data["favorite_service_id"])
        
        return query, params
