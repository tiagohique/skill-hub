# Tarefa 13 — Portal: esqueleto em contêiner, cliente da API e tela Skills

**Fase:** 5 · **Depende de:** 10 · **Commit:** `feat(portal): scaffold, API client and skills list`

## Objetivo
Portal React+Vite rodando em contêiner, falando só com a REST, com a tela de listagem.

## Arquivos
`portal/{Dockerfile,.dockerignore,package.json,package-lock.json,vite.config.ts,tsconfig.json,index.html}`, `portal/src/{main.tsx,App.tsx,api.ts,types.ts,styles.css}`, `portal/src/pages/SkillsPage.tsx`; `docker-compose.yml` (serviço `portal`).

## Interfaces (consome / produz)
`types.ts` espelha os schemas da Tarefa 10. `api.ts`: `listSkills()`, `getSkill(name)`, `getVersion(name, version)`, `uploadSkill(file, version)`, `promote(name, version, to)`, `deprecate(name, version)`; erro lança `ApiError {code, message}`. Navegação por hash (`#/`, `#/skills/<name>`, `#/upload`), sem biblioteca de rotas.

## Regras e valores da spec
`node:22-alpine`; bind mount `./portal:/app` com volume anônimo em `/app/node_modules` (nada de `node_modules` no host); proxy `/api` → `API_TARGET` (`http://hub:8000` no Compose); `lang="pt-BR"`. Tela: nome, domínio, versão `stable`, versão `beta` (traço quando vazio); vazio: "Nenhuma skill publicada ainda."; erro mostra `message`. Sem login.

## Testes
Sem framework de testes no portal (fora da lista de dependências). Verificação = build com `tsc` e checagem no navegador.

## Comandos de verificação
```bash
docker run --rm -v "$PWD/portal:/app" -w /app node:22-alpine npm install
docker compose run --rm portal npm run build
docker compose up --build -d
```

## Critérios de aceite
- [x] Build sem erros de tipo
- [x] `http://localhost:5173` mostra estado vazio e depois a lista

## Notas de execução
Versões resolvidas pelo `npm` no contêiner (React 19, Vite 8, TypeScript 7); o `package-lock.json` foi gerado com `docker run -v $PWD/portal:/app -v /app/node_modules node:22-alpine npm install` (o `node_modules` fica em volume do contêiner). `vite.config.ts` usa `loadEnv` para ler `API_TARGET` (evita `@types/node`) e `src/vite-env.d.ts` declara os tipos de CSS. As rotas de detalhe e upload são placeholders até as Tarefas 14 e 15. Verificado no navegador: lista mostra a skill enviada pelo proxy `/api`.
