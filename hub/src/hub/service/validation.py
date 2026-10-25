"""Validação de upload. Função pura: não grava nada e nunca executa o conteúdo.

Todo conteúdo enviado é entrada não confiável.
"""

import io
import json
import re
import stat
import zipfile
import zlib
from dataclasses import dataclass
from typing import Any

import yaml

from hub.domain.errors import LimitExceededError, SkillValidationError
from hub.domain.models import SkillFile
from hub.domain.semver import is_semver

SKILL_MD = "SKILL.md"
_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_CHUNK = 64 * 1024


@dataclass(frozen=True)
class UploadLimits:
    max_file_bytes: int
    max_bundle_bytes: int
    max_files: int


@dataclass(frozen=True)
class ParsedSkill:
    name: str
    description: str
    frontmatter: dict[str, Any]
    files: tuple[SkillFile, ...]


def parse_upload(filename: str, data: bytes, version: str, limits: UploadLimits) -> ParsedSkill:
    if not is_semver(version):
        raise SkillValidationError(f"Versão inválida '{version}': use semver, por exemplo 1.0.0.")

    lower = filename.lower()
    if lower.endswith(".md"):
        files = _from_md(data, limits)
    elif lower.endswith(".zip"):
        files = _from_zip(data, limits)
    else:
        raise SkillValidationError("Formato não suportado: envie um arquivo .md ou .zip.")

    skill_md = next(f for f in files if f.path == SKILL_MD)
    frontmatter = _parse_frontmatter(skill_md.data)

    name = frontmatter.get("name")
    if not isinstance(name, str) or not _NAME.fullmatch(name):
        raise SkillValidationError(
            "Frontmatter: 'name' é obrigatório e deve ter só minúsculas, números e hífens."
        )
    description = frontmatter.get("description")
    if not isinstance(description, str) or not description.strip():
        raise SkillValidationError("Frontmatter: 'description' é obrigatório.")

    metadata = frontmatter.get("metadata")
    if isinstance(metadata, dict) and "version" in metadata and str(metadata["version"]) != version:
        raise SkillValidationError(
            f"A versão do frontmatter (metadata.version = {metadata['version']}) "
            f"não coincide com a versão informada ({version})."
        )

    return ParsedSkill(
        name=name,
        description=description,
        frontmatter=frontmatter,
        files=tuple(sorted(files, key=lambda f: f.path)),
    )


def _from_md(data: bytes, limits: UploadLimits) -> list[SkillFile]:
    if len(data) > limits.max_file_bytes:
        raise LimitExceededError(f"{SKILL_MD} excede o limite de {limits.max_file_bytes} bytes.")
    return [SkillFile(SKILL_MD, data)]


def _check_path(name: str) -> None:
    parts = name.split("/")
    if (
        name.startswith("/")
        or re.match(r"^[A-Za-z]:", name)
        or "\\" in name
        or any(p in ("", ".", "..") for p in parts)
    ):
        raise SkillValidationError(f"Caminho não permitido no zip: '{name}'.")


def _ignored(name: str) -> bool:
    """Lixo criado pelo Finder do Mac e pastas."""
    return name.endswith("/") or name.startswith("__MACOSX/") or name.split("/")[-1] == ".DS_Store"


def _from_zip(data: bytes, limits: UploadLimits) -> list[SkillFile]:
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile:
        raise SkillValidationError("O arquivo enviado não é um zip válido.") from None

    with zf:
        infos = [i for i in zf.infolist() if not _ignored(i.filename)]

        for info in infos:
            _check_path(info.filename)
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                raise SkillValidationError(
                    f"Links simbólicos não são permitidos: '{info.filename}'."
                )

        names = [i.filename for i in infos]
        for name in names:
            if names.count(name) > 1:
                raise SkillValidationError(f"Arquivo duplicado no zip: '{name}'.")

        prefix = _skill_root(names)
        outside = [n for n in names if not n.startswith(prefix)]
        if outside:
            raise SkillValidationError(f"Arquivo fora da pasta da skill: '{outside[0]}'.")

        if len(infos) > limits.max_files:
            raise LimitExceededError(f"O pacote excede o limite de {limits.max_files} arquivos.")

        files: list[SkillFile] = []
        total = 0
        for info in infos:
            if info.file_size > limits.max_file_bytes:
                raise LimitExceededError(
                    f"'{info.filename}' excede o limite de {limits.max_file_bytes} bytes."
                )
            content = _read_bounded(zf, info, limits, total)
            total += len(content)
            files.append(SkillFile(info.filename.removeprefix(prefix), content))
        return files


def _skill_root(names: list[str]) -> str:
    if SKILL_MD in names:
        return ""
    candidates = [n for n in names if n.endswith("/" + SKILL_MD) and n.count("/") == 1]
    if len(candidates) == 1:
        return candidates[0].removesuffix(SKILL_MD)
    raise SkillValidationError(f"{SKILL_MD} é obrigatório na raiz do zip (ou em uma única pasta).")


def _read_bounded(
    zf: zipfile.ZipFile, info: zipfile.ZipInfo, limits: UploadLimits, total_so_far: int
) -> bytes:
    """Lê em blocos e aborta ao passar dos limites; o tamanho declarado não é confiável."""
    out = bytearray()
    try:
        with zf.open(info) as fh:
            while chunk := fh.read(_CHUNK):
                out += chunk
                if len(out) > limits.max_file_bytes:
                    raise LimitExceededError(
                        f"'{info.filename}' excede o limite de {limits.max_file_bytes} bytes."
                    )
                if total_so_far + len(out) > limits.max_bundle_bytes:
                    raise LimitExceededError(
                        f"O pacote excede o limite de {limits.max_bundle_bytes} bytes."
                    )
    except (zipfile.BadZipFile, zlib.error, RuntimeError, NotImplementedError):
        raise SkillValidationError(f"Não foi possível ler '{info.filename}' do zip.") from None
    return bytes(out)


def _parse_frontmatter(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise SkillValidationError(f"{SKILL_MD} deve estar em UTF-8.") from None

    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines[0].strip() != "---":
        raise SkillValidationError(
            f"{SKILL_MD} deve começar com frontmatter YAML delimitado por '---'."
        )
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise SkillValidationError("O frontmatter não tem o '---' de fechamento.")
    block = "\n".join(lines[1:end])

    try:
        if any(isinstance(e, yaml.AliasEvent) for e in yaml.parse(block)):
            raise SkillValidationError("O frontmatter não pode usar aliases YAML.")
        loaded = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        raise SkillValidationError(f"Frontmatter YAML inválido: {exc}") from None

    if not isinstance(loaded, dict):
        raise SkillValidationError("O frontmatter deve ser um mapa YAML (chave: valor).")
    try:
        result: dict[str, Any] = json.loads(json.dumps(loaded, default=str))
    except TypeError:
        raise SkillValidationError("O frontmatter contém chaves não suportadas.") from None
    return result
