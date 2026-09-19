from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer(auto_error=False)

# In-memory demo user ID for demo mode
DEMO_USER_ID = "demo_investigator_1"


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Returns the authenticated user ID.
    In demo mode (no token or demo_token), returns the demo user.
    Supports Clerk JWT verification if CLERK_JWKS_URL is configured.
    """
    token = credentials.credentials if credentials else None

    # Demo mode: accept demo tokens or no token
    if not token or token in ("demo_token", "demo-token", "test_token") or token.startswith("demo"):
        return DEMO_USER_ID

    # If Clerk is configured, verify the JWT
    from app.core.config import settings
    if settings.CLERK_JWKS_URL:
        try:
            import jwt
            from jwt import PyJWKClient

            jwks_client = PyJWKClient(settings.CLERK_JWKS_URL)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=settings.CLERK_ISSUER_URL,
                options={"verify_aud": False, "require": ["sub", "exp", "iat"]},
            )
            return payload.get("sub", DEMO_USER_ID)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Unknown token in non-Clerk mode — treat as demo user for hackathon
    return DEMO_USER_ID
