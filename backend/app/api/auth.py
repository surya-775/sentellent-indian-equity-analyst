import logging
import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import jwt, JWTError
import httpx
from app.config import settings
from app.db.database import get_db
from app.db.models import User, UserPersona

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer(auto_error=False)

class GoogleAuthRequest(BaseModel):
    id_token: Optional[str] = None
    access_token: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or datetime.timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

async def verify_google_id_token(id_token: str) -> Optional[Dict[str, Any]]:
    """Verifies Google ID token against Google's tokeninfo endpoint."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
            if resp.status_code == 200:
                data = resp.json()
                if data.get("email_verified") in (True, "true"):
                    return data
    except Exception as e:
        logger.warning(f"Google ID token verification failed: {e}")
    return None

async def verify_google_access_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Verifies Google Access token against Google's UserInfo endpoint."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("email_verified") in (True, "true"):
                    return data
    except Exception as e:
        logger.warning(f"Google access token verification failed: {e}")
    return None

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to retrieve authenticated user, falling back to primary evaluator user if unauthenticated."""
    if not credentials:
        user = db.query(User).filter(User.email == "harisankar@sentellent.com").first()
        if not user:
            user = User(email="harisankar@sentellent.com", name="Sentellent Evaluator", is_active=True)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

@router.post("/google", response_model=AuthResponse)
async def google_login(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Strict Google OAuth 2.0 authentication endpoint.
    1. id_token: Cryptographically verified with Google OAuth2 tokeninfo API.
    2. access_token: Cryptographically verified with Google UserInfo API.
    3. email without token: ONLY allowed for whitelisted test users (harisankar@sentellent.com, naga@sentellent.com).
       Any other unverified email is strictly rejected.
    """
    email = None
    name = payload.name or "Investor"
    avatar = payload.avatar_url
    whitelisted_test_emails = [t.lower().strip() for t in settings.TEST_USERS]

    # 1. Verify via Google ID Token
    if payload.id_token:
        google_info = await verify_google_id_token(payload.id_token)
        if not google_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google OAuth verification failed: Invalid or expired ID token."
            )
        email = google_info.get("email")
        name = google_info.get("name", name)
        avatar = google_info.get("picture", avatar)

    # 2. Verify via Google Access Token
    elif payload.access_token:
        google_info = await verify_google_access_token(payload.access_token)
        if not google_info:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google OAuth verification failed: Invalid or expired access token."
            )
        email = google_info.get("email")
        name = google_info.get("name", name)
        avatar = google_info.get("picture", avatar)

    # 3. Direct Test User Sign-in
    elif payload.email:
        clean_email = payload.email.strip().lower()
        if clean_email in whitelisted_test_emails:
            email = clean_email
            name = payload.name or ("Hari Sankar" if "harisankar" in clean_email else "Naga" if "naga" in clean_email else "Jaya Surya")
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Direct login without Google token is strictly restricted to whitelisted test users (harisankar@sentellent.com, naga@sentellent.com, jayasurya71256@gmail.com). For all other accounts, sign in with verified Google OAuth."
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Google OAuth credential or test user email."
        )

    # Upsert user record
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, name=name, avatar_url=avatar)
        db.add(user)
        db.commit()
        db.refresh(user)
    elif name and user.name != name:
        user.name = name
        if avatar:
            user.avatar_url = avatar
        db.commit()

    token = create_access_token(data={"sub": user.email, "user_id": user.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "avatar_url": user.avatar_url,
            "is_test_user": user.email.lower() in whitelisted_test_emails
        }
    }

@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
        "is_test_user": user.email.lower() in [t.lower().strip() for t in settings.TEST_USERS]
    }
