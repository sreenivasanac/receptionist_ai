"""Authentication API endpoints."""
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
import yaml

from app.repositories import user_repo, business_repo
from app.models.user import UserCreate, UserLogin, User

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
    """Register a new user. For business_owner role, also creates a business."""
    if user_repo.username_exists(user_data.username):
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
        
        business_repo.create(
            business_id=business_id,
            name=user_data.business_name,
            business_type=user_data.business_type,
            config_yaml=config_yaml,
            features_enabled={
                "business_info": True,
                "greeting": True,
                "customer_collection": True
            }
        )
    
    user_repo.create(
        user_id=user_id,
        username=user_data.username,
        email=user_data.email,
        role=user_data.role,
        business_id=business_id
    )
    
    return {
        "user_id": user_id,
        "username": user_data.username,
        "role": user_data.role,
        "business_id": business_id,
        "message": "User created successfully"
    }


@router.post("/login", response_model=dict)
async def login(credentials: UserLogin):
    """Login with username and role. No password for MVP - session-based auth."""
    user = user_repo.find_by_username_and_role(credentials.username, credentials.role)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or role")
    
    user_repo.update_last_login(user["id"])
    
    business = None
    if user["business_id"]:
        business = user_repo.get_business_info(user["business_id"])
    
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
    user = user_repo.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
