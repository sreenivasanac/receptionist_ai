"""Authentication API endpoints."""
import uuid
import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
import yaml

from app.db.database import get_db_connection
from app.models.user import UserCreate, UserLogin, User
from app.models.business import Business

router = APIRouter(prefix="/auth", tags=["Authentication"])


def load_vertical_template(vertical: str) -> str:
    """Load the YAML template for a business vertical."""
    template_map = {
        "salon": "beauty",
        "barber": "beauty", 
        "nail": "beauty",
        "beauty": "beauty",
        "medspa": "wellness",
        "wellness": "wellness",
        "massage": "wellness",
        "chiro": "wellness",
        "medical": "medical",
        "dental": "medical",
        "plastic": "medical",
        "dermatology": "medical",
        "fitness": "fitness",
        "gym": "fitness",
        "yoga": "fitness",
        "pilates": "fitness",
    }
    
    template_name = template_map.get(vertical.lower(), "wellness")
    template_path = Path(__file__).parent.parent.parent / "data" / "templates" / f"{template_name}.yaml"
    
    if template_path.exists():
        return template_path.read_text()
    return ""


@router.post("/signup", response_model=dict)
async def signup(user_data: UserCreate):
    """
    Register a new user.
    For business_owner role, also creates a business.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE username = ?", (user_data.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")
        
        user_id = str(uuid.uuid4())
        business_id = None
        
        if user_data.role == "business_owner":
            if not user_data.business_name or not user_data.business_type:
                raise HTTPException(
                    status_code=400, 
                    detail="Business name and type required for business_owner role"
                )
            
            business_id = str(uuid.uuid4())
            config_yaml = load_vertical_template(user_data.business_type)
            
            if config_yaml:
                config = yaml.safe_load(config_yaml)
                config["name"] = user_data.business_name
                config["business_id"] = business_id
                config_yaml = yaml.dump(config)
            
            cursor.execute("""
                INSERT INTO businesses (id, name, type, config_yaml, features_enabled)
                VALUES (?, ?, ?, ?, ?)
            """, (
                business_id,
                user_data.business_name,
                user_data.business_type,
                config_yaml,
                json.dumps({
                    "business_info": True,
                    "greeting": True,
                    "customer_collection": True
                })
            ))
        
        cursor.execute("""
            INSERT INTO users (id, username, email, role, business_id, last_login)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            user_data.username,
            user_data.email,
            user_data.role,
            business_id,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        
        return {
            "user_id": user_id,
            "username": user_data.username,
            "role": user_data.role,
            "business_id": business_id,
            "message": "User created successfully"
        }


@router.post("/login", response_model=dict)
async def login(credentials: UserLogin):
    """
    Login with username and role.
    No password for MVP - session-based auth.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, role, business_id 
            FROM users 
            WHERE username = ? AND role = ?
        """, (credentials.username, credentials.role))
        
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or role")
        
        cursor.execute("""
            UPDATE users SET last_login = ? WHERE id = ?
        """, (datetime.now().isoformat(), user["id"]))
        conn.commit()
        
        business = None
        if user["business_id"]:
            cursor.execute("""
                SELECT id, name, type, address, phone, email, website, features_enabled
                FROM businesses WHERE id = ?
            """, (user["business_id"],))
            biz_row = cursor.fetchone()
            if biz_row:
                business = {
                    "id": biz_row["id"],
                    "name": biz_row["name"],
                    "type": biz_row["type"],
                    "address": biz_row["address"],
                    "phone": biz_row["phone"],
                    "email": biz_row["email"],
                    "website": biz_row["website"],
                    "features_enabled": json.loads(biz_row["features_enabled"] or "{}")
                }
        
        return {
            "user_id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "business_id": user["business_id"],
            "business": business,
            "message": "Login successful"
        }


@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return User(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            business_id=user["business_id"],
            created_at=user["created_at"],
            last_login=user["last_login"]
        )
