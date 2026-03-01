from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.jwt_handler import get_user_from_token

# Reusable security instance
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency to get the current user from JWT token in the Authorization header.
    Decodes the token and returns the user payload.
    """
    token = credentials.credentials
    user = get_user_from_token(token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

def student_required(user: dict = Depends(get_current_user)):
    if user.get("role") != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    return user

def company_required(user: dict = Depends(get_current_user)):
    if user.get("role") != "company":
        raise HTTPException(status_code=403, detail="Company access required")
    return user

def government_required(user: dict = Depends(get_current_user)):
    if user.get("role") != "government":
        raise HTTPException(status_code=403, detail="Government access required")
    return user

def mentor_required(user: dict = Depends(get_current_user)):
    if user.get("role") != "mentor":
        raise HTTPException(status_code=403, detail="Mentor access required")
    return user
