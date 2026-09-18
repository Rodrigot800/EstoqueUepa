# Estrutura do projeto

## Aplicação web atual

```text
frontend/                 Interface usada no navegador
├── public/               Ícones do navegador e do aplicativo instalado
├── src/                  Telas, estilos e componentes React
└── test/                 Testes da interface

backend/                  Regras de negócio e acesso aos dados
├── src/                  API, validação, banco e atualização em tempo real
└── test/                 Testes da API e do PostgreSQL
```

## Arquivos de suporte

```text
assets/                   Logos e identidade visual da UEPA
docs/                     Documentação para manutenção
compose.yaml              Serviços web, API e banco de dados
Dockerfile                Montagem das imagens da aplicação
nginx.conf                Servidor da interface web
.env.example              Modelo de configuração local
README.md                 Manual de instalação e uso
```

## Dados de referência

As planilhas `.xlsx` permanecem no projeto para consulta e importação de dados. Elas não são necessárias para iniciar o sistema web com Docker.

## Boas práticas de manutenção

- Desenvolva novas funções da versão web em `frontend/` e `backend/`.
- Não edite o banco diretamente sem realizar backup.
- Não versione `.env`, `node_modules/` ou arquivos gerados pelo editor.
- Antes de publicar uma alteração, execute `docker compose up -d --build` e confira o sistema em `http://localhost:8080`.
