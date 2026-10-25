---
name: html-landing-page
description: Cria landing pages em HTML puro, acessíveis e responsivas, a partir do template base. Use quando pedirem uma página de apresentação, landing page ou página de produto sem framework.
metadata:
  version: "1.0.0"
  domain: frontend
  owner: time-web
---

# Landing page em HTML

Monte a página a partir de `templates/base.html`. Não use framework nem build: um único arquivo HTML com CSS embutido.

## Passos

1. Copie `templates/base.html` para o destino pedido (por exemplo `index.html`).
2. Troque os trechos `{{ ... }}`: título, resumo, chamada para ação e as três vantagens.
3. Mantenha a estrutura semântica (`header`, `main`, `section`, `footer`) e um único `h1`.
4. Garanta o básico de acessibilidade: `lang` no `html`, `alt` nas imagens, contraste suficiente e foco visível nos links e botões.
5. Teste em largura de celular (375 px) e de desktop. Nada de rolagem horizontal.

## Regras

- Textos da página no idioma do usuário.
- Sem scripts de terceiros nem fontes externas.
- Imagens só se o usuário fornecer; caso contrário, use apenas tipografia e cor.
