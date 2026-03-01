"""JWT Token Handler — Production Grade"""
import os
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from jose import JWTError, jwt

# Ensure .env is loaded from the root directory
base_dir = Path(__file__).parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")

# JWT Configuration
# SECRET_KEY must be stable across restarts
SECRET_KEY = os.getenv("JWT_SECRET", "tn_internfair_super_secret_key_change_in_production_min_32_chars")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT access token.
    :param data: Dictionary containing user claims (user_id, email, role)
    :param expires_delta: Optional expiration time override
    :return: Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS))
    
    # Standard 'exp' claim should be an integer timestamp
    to_encode.update({"exp": int(expire.timestamp())})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """
    Decodes and validates a JWT token.
    Checks signature and expiration automatically.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        # Invalid signature, expired, or malformed token
        return None


def get_user_from_token(token: str) -> Optional[dict]:
    """
    Extracts user information from a validated token payload.
    """
    payload = decode_token(token)
    if not payload:
        return None
        
    return {
        "user_id": payload.get("user_id"),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }
