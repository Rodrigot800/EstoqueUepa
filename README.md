# Estoque UEPA — Campus Castanhal

Sistema web para controle de materiais e movimentações do almoxarifado da **Universidade do Estado do Pará (UEPA), Campus Castanhal**.

Ele foi criado para organizar produtos, registrar entradas e saídas e permitir uma consulta rápida do saldo disponível em cada estoque ou setor.

## O que o sistema faz

- Cadastra produtos, unidade de medida e estoque mínimo.
- Registra entradas e saídas de materiais.
- Calcula o saldo automaticamente pelo histórico de movimentações.
- Destaca produtos sem estoque ou abaixo do estoque mínimo.
- Mantém históricos por produto, tipo de movimentação e período.
- Organiza dados em estoques separados, como **ADM**, laboratórios e outros setores.
- Permite editar e excluir produtos e movimentações com confirmação.
- Atualiza os dados abertos em outros navegadores automaticamente.
- Pode ser instalado pelo navegador como um aplicativo, com a identidade visual da UEPA.

> Ao excluir um produto, todo o histórico dele também é removido. Faça backup antes de uma exclusão importante.

## Como funciona no dia a dia

1. Escolha o estoque desejado no campo **Estoque atual**.
2. Caso necessário, clique em **Adicionar estoque** para criar um novo setor.
3. Clique em **Cadastrar produtos** e informe nome, unidade e estoque mínimo.
4. Clique em **Nova movimentação** para registrar uma ou mais entradas ou saídas.
5. Consulte a tela **Visão do estoque** para acompanhar o saldo e os alertas.
6. Abra **Movimentações** para pesquisar, filtrar, editar ou excluir registros anteriores.

### Regras de saldo

- Toda nova saída precisa ter saldo disponível.
- Uma entrada pode ser corrigida para saída somente se o saldo final não ficar negativo.
- Uma saída pode ser corrigida para entrada mesmo que o produto já possua saldo negativo; isso ajuda a ajustar registros históricos.

## Instalação

### Requisitos

- [Docker Engine](https://docs.docker.com/engine/install/)
- Docker Compose v2

### Primeiro acesso

No terminal, entre na pasta do projeto e execute:

```bash
cp .env.example .env
```

Abra o arquivo `.env` e troque o valor de `POSTGRES_PASSWORD` por uma senha forte. Em seguida, inicie o sistema:

```bash
docker compose up -d --build
```

Abra no navegador:

```text
http://localhost:8080
```

Para acessar em outro computador da mesma rede, use:

```text
http://IP_DA_MAQUINA:8080
```

Substitua `IP_DA_MAQUINA` pelo endereço IP do computador onde o sistema está instalado.

## Instalar como aplicativo

Com o sistema aberto no Chrome ou Edge:

1. Abra o menu do navegador.
2. Escolha **Instalar Estoque UEPA** ou **Instalar aplicativo**.
3. Confirme a instalação.

O sistema poderá ser aberto pela área de trabalho ou pelo menu de aplicativos. A logo quadrada da UEPA é usada como ícone do aplicativo, e a logo específica da aba é usada na guia do navegador.

## Atualizar o sistema após alterações

Sempre que houver mudanças nos arquivos do projeto, execute:

```bash
docker compose up -d --build
```

Depois, atualize o navegador com `Ctrl + F5`. Se o aplicativo já estiver instalado e o ícone tiver mudado, desinstale-o e instale novamente para renovar o atalho.

## Administração e manutenção

### Verificar se está funcionando

```bash
docker compose ps
```

Os serviços `db`, `api` e `web` devem aparecer em execução.

### Ver os registros técnicos

```bash
docker compose logs -f api
```

### Parar o sistema

```bash
docker compose down
```

Esse comando **não apaga os dados**.

> Não use `docker compose down -v` se quiser preservar o banco de dados, pois essa opção remove todos os produtos e movimentações salvos.

### Fazer backup

Execute o comando abaixo na pasta do projeto:

```bash
docker compose exec -T db pg_dump -U estoque -d estoque > backup.sql
```

Guarde o arquivo `backup.sql` em um local seguro, fora da pasta do Docker.

## Importar o estoque IOMM por SQL

O arquivo [import_estoque_iomm.sql](database/imports/import_estoque_iomm.sql) foi gerado a partir da planilha `Estoque IOMM.xlsx`. Ele cria o estoque **IOMM**, inclui 52 produtos e 981 movimentações, preservando as datas originais.

Antes de executar, faça um backup. O script interrompe a importação caso o estoque IOMM já possua produtos, evitando registros duplicados.

```bash
docker compose exec -T db psql -v ON_ERROR_STOP=1 -U estoque -d estoque < database/imports/import_estoque_iomm.sql
```

## Acesso pela rede e segurança

Por padrão, o sistema pode ser acessado no próprio computador e pela rede local. Para que outras pessoas usem o endereço da rede, o computador precisa permanecer ligado e o firewall deve permitir a porta `8080`.

Esta versão não possui login ou perfis de usuário. Portanto, mantenha o sistema restrito à rede institucional até que seja implementado controle de acesso e HTTPS para uma publicação na internet.

## Estrutura do projeto

- `frontend/`: interface web e arquivos da versão instalável.
- `backend/`: API, regras de estoque, banco de dados e testes.
- `assets/`: logos e recursos oficiais da identidade visual.
- `docs/`: orientações complementares para manutenção.
- `*.xlsx`: planilhas preservadas para consulta e importação de dados.
- `compose.yaml`, `Dockerfile` e `nginx.conf`: configuração para executar o sistema com Docker.

Veja [a estrutura detalhada](docs/ESTRUTURA.md) para saber a finalidade de cada pasta antes de alterar arquivos.

## Tecnologia utilizada

- Interface: React e Vite
- API: Node.js e Express
- Banco de dados: PostgreSQL
- Execução: Docker Compose

## Suporte

Em caso de dúvida ou erro, registre qual tela estava usando, a ação realizada e uma captura da mensagem apresentada. Essas informações facilitam a correção.
