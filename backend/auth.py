import os
import json
import urllib.request
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from database import get_db
from sqlalchemy.orm import Session
from models import User
from dotenv import load_dotenv

load_dotenv()

auth_scheme = HTTPBearer(auto_error=False)

CLERK_FRONTEND_API = os.getenv("CLERK_FRONTEND_API", "")
CLERK_SECRET_KEY = os.getenv("CLERK_SECRET_KEY", "")

# We fetch JWKS once and cache it in memory to avoid requesting it every time
_jwks_cache = None


def get_jwks():
    global _jwks_cache
    if _jwks_cache:
        return _jwks_cache

    if not CLERK_FRONTEND_API:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="CLERK_FRONTEND_API not configured on the server.",
        )

    jwks_url = f"{CLERK_FRONTEND_API}/.well-known/jwks.json"

    try:
        req = urllib.request.Request(jwks_url)
        with urllib.request.urlopen(req) as response:
            _jwks_cache = json.loads(response.read())
            return _jwks_cache
    except Exception as e:
        print(f"Error fetching JWKS from {jwks_url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch JWKS: {str(e)}",
        )


def verify_token(token: str):
    """Verify a Clerk JWT token using JWKS. No fallback bypass."""
    jwks = get_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}
        for key in jwks.get("keys", []):
            if key["kid"] == unverified_header.get("kid"):
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }
                break

        if not rsa_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unable to find appropriate signing key.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
):
    """Get the current authenticated user. Returns None if no token provided."""
    if not credentials:
        return None

    token = credentials.credentials
    payload = verify_token(token)

    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.query(User).filter(User.clerk_id == clerk_id).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found in local database. Please sync.",
        )

    return user


def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
):
    """Require authentication. Raises 401 if no token provided."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return get_current_user(credentials=credentials, db=db)
