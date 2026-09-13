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

Abra http://localhost:8080. `WEB_PORT` permite mudar a porta.

```bash
docker compose ps
docker compose logs -f api
docker compose down
```

`docker compose down` preserva o banco. **Não use `down -v` se quiser manter os dados**, pois essa opção remove o volume.

O sistema mantém o modelo de acesso do Python: não há autenticação nem perfis de usuário. Por padrão, a porta fica acessível apenas no computador local (`127.0.0.1`). Para acesso em rede interna, defina `BIND_ADDRESS=0.0.0.0` e recrie o serviço web. Antes de exposição pública, implemente autenticação, autorização e HTTPS. A API e o banco não publicam portas no host.

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

Os testes de integração usam schema temporário e o removem ao terminar; não alteram os produtos do sistema. Cobrem duplicatas, validação, rollback, filtros de datas e concorrência. Sem `DATABASE_URL`, a integração é marcada como ignorada.

## API

| Método | Rota | Uso |
| --- | --- | --- |
| GET | `/api/health` | Disponibilidade da API e do banco |
| GET | `/api/warehouses` | Lista estoques |
| POST | `/api/warehouses` | `{ "name": "ADM" }` |
| GET | `/api/products?warehouseId=1` | Produtos e saldos do estoque |
| POST | `/api/products` | `{ "warehouseId": 1, "products": [{ "name": "Papel A4", "unit": "RESMA", "minimum": 5 }] }` |
| GET | `/api/movements?warehouseId=1` | Histórico do estoque; aceita `from`, `to` (YYYY-MM-DD), `type` e `productId` |
| POST | `/api/movements` | `{ "warehouseId": 1, "movements": [{ "productId": 1, "type": "ENTRADA", "quantity": 10 }] }` |

`warehouseId` é obrigatório nas consultas e gravações de produtos/movimentos. A API rejeita movimentos de produtos pertencentes a outro estoque. Nomes de estoques são únicos, desconsiderando maiúsculas/minúsculas e espaços nas pontas. A separação organiza os dados por local; não é um controle de permissões por usuário.

As listagens retornam todos os registros; para históricos muito grandes, acrescente paginação no servidor. O schema inicial está em `backend/src/schema.sql`; alterações futuras de schema devem ser feitas por migrações versionadas.

## Backup

```bash
docker compose exec -T db pg_dump -U estoque -d estoque > backup.sql
```

Guarde backups fora do volume Docker e verifique a restauração em um banco separado.

Documentação das ferramentas: [Express](https://expressjs.com/en/guide/migrating-5/) e [Vite](https://vite.dev/guide/).
