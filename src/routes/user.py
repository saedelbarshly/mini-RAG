from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from controllers import UserController
from helpers.config import get_settings
from models.UserModel import UserModel
from models.db_schemes import User
from .schemes.user import RegisterRequest
from .dependencies import get_current_user


user_router = APIRouter(
    prefix="/api/v1/user",
    tags=["api_v1", "user"],
)


@user_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(request: Request, register_request: RegisterRequest):
    user_model = await UserModel.create_instance(db_client=request.app.db_client)
    settings = get_settings()
    user_controller = UserController(
        secert_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    email = register_request.email.strip().lower()
    if await user_model.get_user_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user_data = User(
        name=register_request.name,
        email=email,
        password=await user_controller.create_hash_password(register_request.password),
    )

    try:
        user = await user_model.create_user(user=user_data)
    except IntegrityError as exc:
        constraint_name = getattr(exc.orig, "constraint_name", None)
        if constraint_name is None:
            constraint_name = getattr(
                getattr(exc.orig, "diag", None),
                "constraint_name",
                None,
            )
        if constraint_name == "users_email_key":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            ) from exc
        raise

    token = user_controller.create_access_token(
        data={"sub": str(user.user_uuid)}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "user_uuid": str(user.user_uuid),
            "name": user.name,
            "email": user.email,
            "is_verified": user.is_verified,
        },
    }


@user_router.post("/login")
async def user_login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    user_model = await UserModel.create_instance(db_client=request.app.db_client)
    settings = get_settings()
    user_controller = UserController(
        secert_key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    email = form_data.username.strip().lower()
    user = await user_model.get_user_by_email(email=email)
    # verify_password checks a dummy hash when the user is missing, so both
    # failure paths take the same time.
    password_ok = await user_controller.verify_password(
        form_data.password,
        user.password if user is not None else None,
    )
    if user is None or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = user_controller.create_access_token(
        data={"sub": str(user.user_uuid)}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "user_uuid": str(user.user_uuid),
            "name": user.name,
            "email": user.email,
            "is_verified": user.is_verified,
        },
    }


@user_router.get("/profile")
async def get_user_profile(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return {
        "id": current_user.id,
        "user_uuid": str(current_user.user_uuid),
        "name": current_user.name,
        "email": current_user.email,
        "is_verified": current_user.is_verified,
    }
