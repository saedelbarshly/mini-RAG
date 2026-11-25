from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from controllers import UserController
from helpers.config import get_settings
from models.UserModel import UserModel
from models.db_schemes import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/user/login")


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Resolve the bearer token to a User, or raise 401.

    Add `Depends(get_current_user)` to any route that needs authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    settings = get_settings()
    user_controller = UserController(
        secert_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    subject = user_controller.verify_access_token(token)
    if subject is None:
        raise credentials_exception

    try:
        user_uuid = UUID(subject)
    except ValueError:
        raise credentials_exception

    user_model = await UserModel.create_instance(db_client=request.app.db_client)
    user = await user_model.get_user_by_uuid(user_uuid)
    if user is None:
        raise credentials_exception
    return user
