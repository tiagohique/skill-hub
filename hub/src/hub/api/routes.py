"""Adaptador REST (FastAPI). Só traduz HTTP; a regra de negócio está no SkillService."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from hub.api.auth import CurrentUser
from hub.api.schemas import (
    PromoteIn,
    SkillDetailOut,
    SkillSummaryOut,
    VersionDetailOut,
)
from hub.config import Settings
from hub.domain.errors import LimitExceededError
from hub.domain.models import Status
from hub.service.skill_service import SkillService

router = APIRouter(prefix="/api")


def get_service(request: Request) -> SkillService:
    service: SkillService = request.app.state.service
    return service


def get_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


Service = Annotated[SkillService, Depends(get_service)]


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/skills/upload", status_code=201, response_model=VersionDetailOut)
async def upload(
    service: Service,
    user: CurrentUser,
    settings: Annotated[Settings, Depends(get_settings)],
    file: Annotated[UploadFile, File()],
    version: Annotated[str, Form()],
) -> VersionDetailOut:
    # Lê no máximo o limite do pacote + 1 byte: nunca carrega um envio gigante inteiro.
    data = await file.read(settings.max_bundle_bytes + 1)
    if len(data) > settings.max_bundle_bytes:
        raise LimitExceededError(f"O envio excede o limite de {settings.max_bundle_bytes} bytes.")
    detail = await service.upload(
        filename=file.filename or "", data=data, version=version, actor=user.username
    )
    return VersionDetailOut.model_validate(detail)


@router.get("/skills", response_model=list[SkillSummaryOut])
async def list_skills(service: Service, user: CurrentUser) -> list[SkillSummaryOut]:
    return [SkillSummaryOut.model_validate(s) for s in await service.list_skills()]


@router.get("/skills/{name}", response_model=SkillDetailOut)
async def get_skill(name: str, service: Service, user: CurrentUser) -> SkillDetailOut:
    return SkillDetailOut.model_validate(await service.get_skill(name))


@router.get("/skills/{name}/versions/{version}", response_model=VersionDetailOut)
async def get_version(
    name: str, version: str, service: Service, user: CurrentUser
) -> VersionDetailOut:
    return VersionDetailOut.model_validate(await service.get_version(name, version))


@router.post("/skills/{name}/versions/{version}/promote", response_model=VersionDetailOut)
async def promote(
    name: str, version: str, body: PromoteIn, service: Service, user: CurrentUser
) -> VersionDetailOut:
    detail = await service.promote(name, version, Status(body.to), user.username)
    return VersionDetailOut.model_validate(detail)


@router.post("/skills/{name}/versions/{version}/deprecate", response_model=VersionDetailOut)
async def deprecate(
    name: str, version: str, service: Service, user: CurrentUser
) -> VersionDetailOut:
    return VersionDetailOut.model_validate(await service.deprecate(name, version, user.username))
