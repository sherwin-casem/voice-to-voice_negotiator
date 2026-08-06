from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import inspect as sa_inspect

from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.db.models.user import User
from app.modules.auth.deps import get_auth_service, get_current_user
from app.modules.auth.service import AuthService
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/auth", tags=["auth"])


def _user_response(user: User) -> UserResponse:
    display_name = None
    if "profile" not in sa_inspect(user).unloaded:
        profile = user.profile
        display_name = profile.display_name if profile else None
    return UserResponse(id=str(user.id), email=user.email, display_name=display_name)


def _auth_response(user: User, access_token: str) -> AuthResponse:
    return AuthResponse(access_token=access_token, user=_user_response(user))


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    max_age = settings.jwt_refresh_ttl_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=max_age,
        path="/",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=settings.auth_cookie_name, path="/")


@router.post("/register", response_model=ApiResponse[AuthResponse])
async def register(
    body: RegisterRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[AuthResponse]:
    user, access_token, refresh_token = await service.register(body.email, body.password)
    _set_refresh_cookie(response, refresh_token)
    return ApiResponse(data=_auth_response(user, access_token))


@router.post("/login", response_model=ApiResponse[AuthResponse])
async def login(
    body: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[AuthResponse]:
    user, access_token, refresh_token = await service.login(body.email, body.password)
    _set_refresh_cookie(response, refresh_token)
    return ApiResponse(data=_auth_response(user, access_token))


@router.post("/logout", response_model=ApiResponse[dict[str, bool]])
async def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[dict[str, bool]]:
    token = request.cookies.get(settings.auth_cookie_name)
    await service.logout(token)
    _clear_refresh_cookie(response)
    return ApiResponse(data={"success": True})


@router.post("/refresh", response_model=ApiResponse[AuthResponse])
async def refresh_tokens(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[AuthResponse]:
    token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise UnauthorizedError("Refresh token missing")
    user, access_token, new_refresh = await service.refresh(token)
    _set_refresh_cookie(response, new_refresh)
    return ApiResponse(data=_auth_response(user, access_token))


@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)) -> ApiResponse[UserResponse]:
    return ApiResponse(data=_user_response(current_user))
