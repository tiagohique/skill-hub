# Tarefa 04 — Validação de upload

**Fase:** 1 · **Depende de:** 03 · **Commit:** `feat(service): upload validation for SKILL.md and zip`

## Objetivo
Função pura que valida `.md` e `.zip` e devolve a skill pronta para gravar. Skill é dado não confiável; nunca executar nada.

## Arquivos
`hub/src/hub/service/validation.py`; `hub/tests/unit/test_validation.py` (zips montados em memória).

## Interfaces (consome / produz)
Consome `SkillFile`, `SkillValidationError`, `LimitExceededError`, `is_semver`. Produz `UploadLimits(max_file_bytes, max_bundle_bytes, max_files)`, `ParsedSkill(name, description, frontmatter, files)` e `parse_upload(filename, data, version, limits) -> ParsedSkill`.

## Regras e valores da spec
- `.md` (case-insensitive) → um arquivo `SKILL.md`; `.zip` → pacote; outra extensão → erro.
- Zip: ignora diretórios, `__MACOSX/**` e `.DS_Store`; rejeita caminho absoluto, `\`, `..`, symlink (`external_attr>>16 & 0o170000 == 0o120000`) e duplicados. Raiz = raiz do zip com `SKILL.md`, ou pasta única de topo com `SKILL.md` (prefixo removido); qualquer outro arquivo fora da raiz → erro.
- Limites: arquivos lidos em blocos de 64 KiB e abortados ao passar `max_file_bytes`; soma abortada em `max_bundle_bytes`; `MAX_FILES`. Estouro → `LimitExceededError`.
- Frontmatter: UTF-8 sem BOM, CRLF normalizado só para o parse, `---` de abertura e fechamento, `yaml.safe_load` deve ser `dict`; `name` `^[a-z0-9]+(-[a-z0-9]+)*$`; `description` string não vazia; `str(metadata.version) == version` se existir; `version` semver. Bytes gravados são os originais.
- Mensagens em pt-BR citando arquivo/campo.

## Testes
Um por regra: `.md` válido; zip na raiz; zip com pasta única; **zip do Finder** aceito; sem `SKILL.md`; `../evil`, `/abs`, `a\b`, symlink, duplicado, fora da pasta; 101 arquivos; **tamanho declarado mentiroso**; soma acima do bundle; BOM+CRLF aceito; sem fechamento `---`; frontmatter lista; YAML inválido; `metadata.version: 1.0` vs `1.0.0`; `name: My_Skill`; versão `1.0`; extensão `.txt`.

## Comandos de verificação
```bash
docker compose run --rm hub-test pytest tests/unit/test_validation.py -v
```

## Critérios de aceite
- [ ] Todos os testes verdes; ruff e mypy limpos
- [ ] Review Focus 1, 2 e 4 cobertos por teste

## Notas de execução
—
