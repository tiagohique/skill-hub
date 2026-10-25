---
name: fastapi-endpoint
description: Adiciona um endpoint REST em FastAPI seguindo a arquitetura em camadas (rota fina, regra no serviço, SQL no repositório) com testes. Use ao criar ou alterar rotas de uma API Python.
metadata:
  version: "1.0.0"
  domain: backend
  owner: time-api
---

# Endpoint FastAPI em camadas

Antes de começar, leia `reference/checklist.md`.

## Passos

1. **Teste primeiro.** Escreva o teste da rota (sucesso e erros) e veja falhar.
2. **Schemas.** Crie os modelos pydantic de entrada e saída. Nunca devolva objetos do banco direto.
3. **Serviço.** Coloque a regra de negócio numa classe de serviço. A rota só traduz HTTP.
4. **Repositório.** Só ele fala SQL. O serviço nunca monta consulta.
5. **Rota.** Chame o serviço, converta erros de domínio em respostas `{"code": "...", "message": "..."}` e use o status HTTP certo (201 ao criar, 409 em conflito, 404 quando não existir).
6. **Rode** testes, lint e tipos até ficarem limpos.

## Regras

- Camada de cima chama a de baixo; nunca o contrário.
- Operações que alteram vários registros usam uma única transação.
- Mensagens de erro para o usuário em português do Brasil; identificadores em inglês.
