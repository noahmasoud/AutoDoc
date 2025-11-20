"""FastAPI router for authentication.

Implements:
- POST /api/login - User login with JWT token generation
- GET /api/userinfo - Get current user info (protected)
"""

import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/login", tags=["auth"])
security = HTTPBearer()

# For development: Simple user database
# In production, this would be in a database with hashed passwords
DEV_USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",  # In production, use bcrypt hashed passwords
        "email": "admin@autodoc.dev",
    },
    "demo": {"username": "demo", "password": "demo123", "email": "demo@autodoc.dev"},
    "user": {"username": "user", "password": "user123", "email": "user@autodoc.dev"},
}


class LoginRequest(BaseModel):
    """Request model for login."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Response model for login."""

    access_token: str
    token_type: str = "bearer"


class UserInfo(BaseModel):
    """User information model."""

    username: str
    email: str


def create_access_token(username: str) -> str:
    """
    Create JWT access token.

    Args:
        username: Username to encode in token

    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(hours=24)  # Token valid for 24 hours
    to_encode = {"sub": username, "exp": expire, "iat": datetime.utcnow()}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Verify JWT token and return username.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        Username from token

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )
        return username
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        ) from err


@router.post("", response_model=LoginResponse)
def login_endpoint(request: LoginRequest):
    """
    Authenticate user and return JWT token.

    For development, accepts these credentials:
    - admin / admin123
    - demo / demo123
    - user / user123

    In production, this should verify against a database with hashed passwords.
    """
    # Check if user exists and password matches
    user = DEV_USERS.get(request.username)

    if not user or user["password"] != request.password:
        logger.warning(f"Failed login attempt for username: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    # Create JWT token
    access_token = create_access_token(request.username)

    logger.info(f"Successful login for user: {request.username}")

    return LoginResponse(access_token=access_token, token_type="bearer")


@router.get("", response_model=UserInfo)
def get_current_user(username: str = Depends(verify_token)):
    """
    Get current user information (protected endpoint).

    Alias of /api/login/userinfo to support legacy clients that call GET /api/login
    for token validation.
    """
    user = DEV_USERS.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserInfo(username=user["username"], email=user["email"])


@router.get("/userinfo", response_model=UserInfo)
def get_user_info(username: str = Depends(verify_token)):
    """
    Get current user information (protected endpoint).

    Requires valid JWT token in Authorization header.
    """
    user = DEV_USERS.get(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserInfo(username=user["username"], email=user["email"])
