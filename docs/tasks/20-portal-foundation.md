# Tarefa 20 — Portal: fundação (Tailwind), layout e badges

**Fase:** facelift · **Depende de:** 19 · **Commit:** `feat(portal): Tailwind foundation, layout and badges`

## Objetivo
Instalar Tailwind e lucide-react (aprovados pelo usuário), definir o tema dark e entregar a navbar global e o componente Badge.

## Arquivos
Criar `portal/src/components/{Layout,Badge}.tsx`. Alterar `portal/package.json` e `package-lock.json`, `portal/vite.config.ts`, `portal/index.html`, `portal/src/styles.css`, `portal/src/App.tsx`.

## Interfaces (consome / produz)
`Layout({active, children})` com `active: "list" | "upload" | null`; `Badge({type, children})` com `type: "stable"|"beta"|"draft"|"domain"|"deprecated"|"retired"` (sem filhos mostra `-`).

## Regras e valores da spec
Navbar sticky 64 px, borda zinc-800, logo `Box` + "Skills Hub", links "Skills"/"Enviar skill" (ativo zinc-800/50), hambúrguer abaixo de `md` (menu `fixed`, itens ≥ 44 px, `aria-expanded`, fecha ao navegar e com Esc). Cores: zinc-950/900/800, texto zinc-50/400, indigo-500. Dark nativo.

## Testes
Sem teste unitário (visual). Verificação: build e navegador.

## Comandos de verificação
```bash
docker compose run --rm --no-deps portal npm run build
docker compose up -d --build -V portal
```

## Critérios de aceite
- [x] Build sem erro de tipo
- [x] Navbar igual ao protótipo em desktop e celular

## Notas de execução
Dependências instaladas em contêiner (`tailwindcss` e `@tailwindcss/vite` 4.3.3, `lucide-react` 1.61): o `node_modules` do contêiner `portal` fica desatualizado até `docker compose build portal` (e `up -V` para renovar o volume anônimo). O CSS antigo foi removido; as telas ainda no estilo antigo ficam sem estilo até as Tarefas 21 a 23. O layout é conferido no navegador junto da Tarefa 21.
