from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from backend.database import db_connection
from backend.utils import security
from backend.services import audit_service

router = APIRouter(prefix="/api/users", tags=["Users"])
security_scheme = HTTPBearer()

# Pydantic Schemas
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    phone: str = ""
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    phone: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """
    Dependency to validate JWT token and return active user profile.
    Raises 401 Unauthorized if invalid.
    """
    token = credentials.credentials
    try:
        payload = security.verify_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials token payload"
            )
            
        user = db_connection.execute_read(
            "SELECT user_id, name, email, phone, role FROM users WHERE email = %s",
            (email,)
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User associated with token no longer exists"
            )
        return user[0]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials token"
        )

def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency to enforce Admin access controls.
    """
    if current_user.get("role") != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Admin privileges required."
        )
    return current_user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user: UserRegister, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    # Check if email already exists
    existing = db_connection.execute_read(
        "SELECT * FROM users WHERE email = %s",
        (user.email,)
    )
    if existing:
        audit_service.log_action(None, "user_registration_failed", client_ip, "Failed", f"Email {user.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    password_hash = security.hash_password(user.password)
    
    # First user registered in system automatically becomes Admin (standard bootstrap pattern!)
    total_users = db_connection.execute_read("SELECT COUNT(*) as count FROM users")[0]["count"]
    role = "Admin" if total_users == 0 else "User"
    
    # Insert new user
    user_id = db_connection.execute_query(
        "INSERT INTO users (name, email, phone, password_hash, role) VALUES (%s, %s, %s, %s, %s)",
        (user.name, user.email, user.phone, password_hash, role)
    )
    
    audit_service.log_action(user_id, "user_registered", client_ip, "Success", f"Role: {role}")
    
    return {
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": role
    }

@router.post("/login", response_model=LoginResponse)
def login_user(credentials: UserLogin, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    
    user = db_connection.execute_read(
        "SELECT * FROM users WHERE email = %s",
        (credentials.email,)
    )
    
    if not user:
        audit_service.log_action(None, "user_login_failed", client_ip, "Failed", f"User {credentials.email} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    user_data = user[0]
    
    if not security.verify_password(credentials.password, user_data["password_hash"]):
        audit_service.log_action(user_data["user_id"], "user_login_failed", client_ip, "Failed", "Incorrect password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
        
    # Generate JWT Token
    token_data = {"sub": user_data["email"], "role": user_data["role"]}
    access_token = security.create_access_token(data=token_data)
    
    audit_service.log_action(user_data["user_id"], "user_login_success", client_ip, "Success")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user_data["user_id"],
            "name": user_data["name"],
            "email": user_data["email"],
            "phone": user_data["phone"],
            "role": user_data["role"]
        }
    }

@router.get("/profile", response_model=UserResponse)
def get_user_profile(current_user: dict = Depends(get_current_user)):
    return current_user
