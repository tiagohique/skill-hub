"""Login por cookie de sessão. Adaptador fino: a regra está no AuthService."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from hub.api.schemas import LoginIn, ThemeIn, UserOut
from hub.domain.models import User
from hub.service.auth_service import SESSION_DAYS, AuthService

COOKIE = "hub_session"

router = APIRouter(prefix="/api/auth")


def get_auth(request: Request) -> AuthService:
    auth: AuthService = request.app.state.auth
    return auth


Auth = Annotated[AuthService, Depends(get_auth)]


async def current_user(request: Request, auth: Auth) -> User:
    return await auth.user_for_token(request.cookies.get(COOKIE))


CurrentUser = Annotated[User, Depends(current_user)]


@router.post("/login", response_model=UserOut)
async def login(body: LoginIn, response: Response, auth: Auth) -> UserOut:
    token, user = await auth.login(body.username.strip(), body.password)
    response.set_cookie(
        COOKIE,
        token,
        max_age=SESSION_DAYS * 24 * 3600,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return UserOut.model_validate(user)


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, auth: Auth) -> None:
    await auth.logout(request.cookies.get(COOKIE))
    response.delete_cookie(COOKIE, path="/")


@router.get("/me", response_model=UserOut)
async def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.put("/theme", response_model=UserOut)
async def set_theme(body: ThemeIn, user: CurrentUser, auth: Auth) -> UserOut:
    return UserOut.model_validate(await auth.set_theme(user, body.theme))
