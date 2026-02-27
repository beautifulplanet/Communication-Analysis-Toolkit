"""Authentication module for the API."""
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from api.config import get_settings

security = HTTPBasic()


def get_current_username(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    """Verify HTTP Basic Auth credentials."""
    settings = get_settings()
    correct_username = settings.auth_username
    correct_password = settings.auth_password

    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
