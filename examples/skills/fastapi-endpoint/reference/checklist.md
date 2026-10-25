# Checklist de endpoint

- [ ] Teste de sucesso e de cada erro esperado (404, 409, 422)
- [ ] Schemas de entrada e saída com tipos explícitos
- [ ] Regra de negócio no serviço, não na rota
- [ ] SQL apenas no repositório
- [ ] Erros no formato `{"code", "message"}`
- [ ] Transação única quando há mais de uma escrita
- [ ] Sem segredos nem dados pessoais em logs
- [ ] Lint e tipos limpos
