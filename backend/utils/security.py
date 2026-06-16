import os
import jwt
import bcrypt
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("security_utils")

# Load configuration values
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "enterprise_super_secret_key_change_me_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def hash_password(password: str) -> str:
    """Hashes password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception as e:
        logger.error(f"Error checking password: {e}")
        return False

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Generates a JWT access token containing payload data."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> dict:
    """
    Decodes and validates a JWT token.
    Returns decoded payload dict if valid, otherwise raises jwt.PyJWTError.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError as e:
        logger.warning("Token expired signature")
        raise e
    except jwt.PyJWTError as e:
        logger.warning(f"Invalid token decode error: {e}")
        raise e
