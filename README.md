# Estoque UEPA — aplicação web

Versão web baseada no aplicativo Python/Tkinter deste repositório. Os arquivos Python e a planilha original foram preservados.

## Tecnologias

- React 19 com Vite, ícones Lucide e CSS responsivo.
- Node.js 22 com Express 5, validação Zod e driver `pg`.
- PostgreSQL 17, com saldos calculados pelo histórico de movimentações.
- Docker Compose: Nginx para o frontend, API Node e banco com volume persistente.

## Executar com Docker

Requisitos: Docker Engine e Docker Compose v2.

```bash
cp .env.example .env
# Edite POSTGRES_PASSWORD no .env antes de iniciar.
docker compose up -d --build
```

Abra http://localhost:8080 no servidor ou `http://IP_DA_MAQUINA:8080` nos outros computadores da rede. `WEB_PORT` permite mudar a porta. A API e os eventos usam caminhos relativos (`/api`), portanto não há IP fixado no código. Se o endereço da máquina mudar, use o novo IP no navegador; nenhuma reconstrução da aplicação é necessária. Para manter também a URL constante, configure um nome DNS na rede ou reserva DHCP no roteador.

```bash
docker compose ps
docker compose logs -f api
docker compose down
```

`docker compose down` preserva o banco. **Não use `down -v` se quiser manter os dados**, pois essa opção remove o volume.

O sistema mantém o modelo de acesso do Python: não há autenticação nem perfis de usuário. `BIND_ADDRESS=0.0.0.0` disponibiliza a aplicação em todas as interfaces IPv4 da máquina, incluindo localhost e a rede local. `DB_BIND_ADDRESS=0.0.0.0` faz o mesmo com o banco, protegido pela senha. A API é acessada pelo Nginx, sem porta própria no host. Antes de exposição pública, implemente autenticação, autorização e HTTPS. Para restringir o acesso ao computador local, altere os endereços de bind para `127.0.0.1`.

## Conectar pelo DBeaver

Crie uma conexão PostgreSQL com os seguintes dados:

| Campo | Mesmo computador | Outro computador da rede |
| --- | --- | --- |
| Host | `localhost` ou `127.0.0.1` | IP atual da máquina que executa o Docker |
| Porta | `5434` | `5434` |
| Banco | `estoque` | `estoque` |
| Usuário | `estoque` | `estoque` |
| Senha | Valor de `POSTGRES_PASSWORD` no `.env` | O mesmo valor |

Use somente o valor da senha, sem `POSTGRES_PASSWORD=` e sem aspas delimitadoras. Clique em **Testar conexão** e instale o driver quando solicitado. As tabelas estão no schema `public`.

A porta do host é definida por `DB_PORT` (padrão `5434`); dentro do Docker o PostgreSQL continua em `5432`. A porta `5433` deste computador já era usada pelo banco `hydrazil_db`, de outro projeto. Conectar a ela com as credenciais do Estoque UEPA resulta em erro de autenticação.

```bash
# Testa as credenciais do .env sem imprimir a senha:
docker compose run --rm --no-deps api npm run db:check -w backend
# Confere quais portas este projeto publicou:
docker compose ps
```

A senha passa à API por `PGPASSWORD`, sem composição de URL; caracteres especiais não precisam ser codificados. Em instalações já inicializadas, editar somente `POSTGRES_PASSWORD` no `.env` não muda a senha gravada no volume PostgreSQL. Para trocar a senha, execute `docker compose exec db psql -U estoque -d estoque`, use `\password estoque`, atualize o `.env` com o mesmo valor e recrie os serviços com `docker compose up -d`. Não apague o volume para corrigir autenticação.

Caso o acesso funcione no servidor mas não em outra máquina, confira se ambos estão na mesma rede e se o firewall permite TCP 8080 (sistema) e 5434 (DBeaver). Não é necessário alterar o IP da rede Docker nem configurar IP estático para os contêineres.

## Funcionalidades

- Criação de estoques por setor ou local (ADM, IOOM etc.), sem limite fixo de quantidade, pelo botão **Adicionar estoque**.
- Seletor **Estoque atual** com última escolha salva no navegador. Produtos, indicadores e histórico mostram somente o estoque selecionado.
- Cadastro de até 100 produtos por lote, com nome único dentro do estoque, unidade e estoque mínimo. O mesmo nome pode ser usado em estoques diferentes.
- Entradas e saídas em lote, com remoção de itens antes da confirmação.
- Consulta e busca de produtos; ordenação por nome, código ou saldo.
- Alertas de saldo zerado/negativo ou abaixo do mínimo.
- Histórico com busca por produto, tipo e intervalo de datas inclusivo, no fuso de Belém.
- Indicadores de produtos, reposição e número de entradas/saídas no mês.
- Mensagens de erro, estados vazios e interface adaptada para celulares.
- Atualização em tempo real nos navegadores abertos após cadastros e movimentações, preservando filtros e rascunhos em andamento.

## Atualização entre usuários

Triggers do PostgreSQL publicam eventos somente depois que a transação é confirmada. Cada API recebe os eventos por `LISTEN/NOTIFY` e os repassa aos navegadores por Server-Sent Events (`/api/events`). Isso também cobre alterações confirmadas pelo DBeaver, importações e múltiplas instâncias da API. Transações desfeitas não publicam alterações.

Os clientes buscam novamente os dados do estoque selecionado, sem recarregar a página ou apagar o formulário aberto. O PostgreSQL continua validando o saldo no momento da gravação: se outro usuário retirar o material enquanto um formulário está aberto, uma saída sem saldo será recusada.

Há reconexão automática, nova consulta ao recuperar a conexão ou retornar à aba e uma consulta de segurança a cada 15 segundos. O indicador mostra se a conexão de eventos está ativa. Atualizações automáticas são de **dados**; alterações no código ainda exigem `docker compose up -d --build`.

Referências: [NOTIFY e confirmação de transações](https://www.postgresql.org/docs/current/sql-notify.htm) e [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events).

Os lotes são transacionais: se um item falhar, nada é salvo. Produtos são bloqueados em ordem de ID durante a gravação de movimentos para impedir que retiradas simultâneas consumam o mesmo saldo. Novas movimentações exigem quantidades inteiras positivas e não podem resultar em saldo negativo. Produtos começam com saldo zero; registre uma entrada para adicionar estoque.

As colunas de “média” da interface Python não tinham cálculo implementado. Na web, os indicadores são identificados como contagem de movimentações mensais; não somam unidades diferentes.

## Importar a planilha Python

A atualização para múltiplos estoques mantém todos os produtos e movimentos existentes em **Estoque geral**, sem alterar IDs ou saldos. Novos estoques começam vazios. A importação legada também usa o Estoque geral e continua exigindo que não existam produtos ou movimentos no banco.

A importação é opcional, feita por comando, e aceita somente banco vazio. Não ocorre automaticamente na inicialização. Ela preserva IDs e datas, valida referências, mantém saldos legados negativos com aviso e calcula o saldo pelo histórico, como o Python. Movimentos com quantidade zero são ignorados com aviso. Qualquer erro interrompe toda a importação.

O cadastro antigo invertia Unidade e Qtd_Mínima. O importador reconhece esse caso quando a terceira coluna é numérica e a quarta contém a unidade textual; cada correção é apresentada no relatório. Formatos ambíguos devem ser revisados em uma cópia da planilha.

```bash
# Copiar a planilha para o contêiner não altera o arquivo original.
docker compose cp estoque.xlsx api:/tmp/estoque.xlsx
# Conferir o relatório antes de gravar:
docker compose exec api npm run import -w backend -- /tmp/estoque.xlsx --dry-run
# Executar a importação:
docker compose exec api npm run import -w backend -- /tmp/estoque.xlsx
```

Para outra planilha, substitua o caminho no comando `cp`. Abas esperadas: `produtos` (ID, Nome, Unidade, Qtd_Mínima, Estoque) e `movimentos` (ID, ProdutoID, ProdutoNome, Tipo, Quantidade, Data). Datas legadas sem fuso são interpretadas como horário de Belém (UTC−3).

## Desenvolvimento sem Docker

Com Node >=22.12, npm e PostgreSQL disponíveis:

```bash
npm ci
export DATABASE_URL='postgresql://usuario:senha@localhost:5432/estoque'
npm run dev:api
# Em outro terminal:
npm run dev:web
```

Vite atende em http://localhost:5173 e encaminha `/api` à porta 3000. A API cria o schema na inicialização. A fonte DM Sans é opcional e possui fallback local caso a rede não esteja disponível.

## Verificação

```bash
npm run build
npm test
# Com o Docker em execução, inclui os testes de integração:
docker compose exec api npm test
```

Os testes de integração usam schema temporário e o removem ao terminar; não alteram os produtos do sistema. Cobrem duplicatas, validação, rollback, filtros, concorrência, migração, isolamento entre estoques, eventos para clientes de duas APIs, SQL direto e reconexão do listener. Sem `DATABASE_URL` ou `PGHOST`, a integração é marcada como ignorada.

## API

| Método | Rota | Uso |
| --- | --- | --- |
| GET | `/api/health` | Disponibilidade da API e do banco |
| GET | `/api/events` | Eventos SSE: `ready`, `change` e `status` |
| GET | `/api/warehouses` | Lista estoques |
| POST | `/api/warehouses` | `{ "name": "ADM" }` |
| GET | `/api/products?warehouseId=1` | Produtos e saldos do estoque |
| POST | `/api/products` | `{ "warehouseId": 1, "products": [{ "name": "Papel A4", "unit": "RESMA", "minimum": 5 }] }` |
| PUT | `/api/products/:id` | Atualiza nome, unidade e estoque mínimo; requer `warehouseId` no corpo |
| DELETE | `/api/products/:id` | Exclui o produto e todo o seu histórico; requer `warehouseId` no corpo |
| GET | `/api/movements?warehouseId=1` | Histórico do estoque; aceita `from`, `to` (YYYY-MM-DD), `type` e `productId` |
| POST | `/api/movements` | `{ "warehouseId": 1, "movements": [{ "productId": 1, "type": "ENTRADA", "quantity": 10 }] }` |
| PUT | `/api/movements/:id` | Atualiza tipo e quantidade; requer `warehouseId` no corpo |
| DELETE | `/api/movements/:id` | Exclui uma movimentação sem permitir saldo negativo; requer `warehouseId` no corpo |

`warehouseId` é obrigatório nas consultas e gravações de produtos/movimentos. A API rejeita movimentos de produtos pertencentes a outro estoque. Nomes de estoques são únicos, desconsiderando maiúsculas/minúsculas e espaços nas pontas. A separação organiza os dados por local; não é um controle de permissões por usuário.

As listagens retornam todos os registros; para históricos muito grandes, acrescente paginação no servidor. O schema inicial está em `backend/src/schema.sql`; alterações futuras de schema devem ser feitas por migrações versionadas.

## Backup

```bash
docker compose exec -T db pg_dump -U estoque -d estoque > backup.sql
```

Guarde backups fora do volume Docker e verifique a restauração em um banco separado.

Documentação das ferramentas: [Express](https://expressjs.com/en/guide/migrating-5/) e [Vite](https://vite.dev/guide/).
