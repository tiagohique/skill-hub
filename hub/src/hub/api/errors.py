from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from hub.domain.errors import HubError

STATUS_BY_CODE = {
    "invalid_skill": 422,
    "limit_exceeded": 413,
    "version_exists": 409,
    "invalid_transition": 409,
    "not_found": 404,
    "unauthorized": 401,
    "invalid_request": 422,
    "integrity_error": 500,
}


def error_response(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"code": code, "message": message})


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(HubError)
    async def hub_error(_: Request, exc: HubError) -> JSONResponse:
        return error_response(STATUS_BY_CODE.get(exc.code, 500), exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = ", ".join(".".join(str(p) for p in e["loc"][1:]) or "corpo" for e in exc.errors())
        return error_response(422, "invalid_request", f"Requisição inválida: {fields}.")

    @app.exception_handler(StarletteHTTPException)
    async def http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        message = "Recurso não encontrado." if exc.status_code == 404 else str(exc.detail)
        return error_response(exc.status_code, code, message)
