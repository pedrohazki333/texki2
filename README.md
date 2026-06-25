# TEXKI2

Sistema interno da Livreprint para controle de produção e administração de pedidos de DTF têxtil. Reconstrução do "Texki" antigo (Laravel + Blade) sobre uma stack moderna e escalável. Uso interno, ~10 usuários (vendedoras, impressor, administradores).

> **Documentação de produto e arquitetura** (leia antes de implementar):
> - [PRD](docs/PRD-TEXKI2.md) — requisitos (o quê)
> - [Design doc](docs/design-doc.md) — arquitetura, modelo de dados, fluxos (o como)
> - [Mini-spec RF5](docs/minispec-RF5.md) — verificação de proporção da arte
> - [Roadmap de fatias](docs/roadmap-fatias.md) — ordem de construção
> - [ADRs](docs/adr/) — decisões e seus porquês
> - [CLAUDE.md](CLAUDE.md) — convenções e invariantes não-negociáveis

## Stack

- **Frontend** — Next.js 15 (App Router) + TypeScript + Tailwind + shadcn/ui
- **Backend** — FastAPI (Python 3.12) + SQLAlchemy 2 + Alembic
- **Banco** — PostgreSQL 16
- **Proxy** — Caddy 2 (HTTPS automático)
- **Arquivos** — filesystem da VPS, atrás de `backend/app/storage/`
- **Deploy** — Docker Compose

## Organização do repositório

```
texki2/
├── docker-compose.yml            # 4 serviços: proxy, web, api, db
├── Caddyfile                     # roteamento HTTPS (/ → web, /api/* → api)
├── deploy.sh                     # pull → build → up → migrate → seed
├── .env.example                  # modelo de variáveis (copie para .env)
├── backend/                      # FastAPI (regras de negócio em services/)
│   └── app/{api,core,db,models,schemas,services,storage}
├── frontend/                     # Next.js (App Router)
│   └── app/{login,(protected)/dashboard}
├── docs/                         # PRD, design doc, ADRs, mini-specs, roadmap
└── uploads/                      # bind mount para artes (vazio nesta fatia)
```

## Pré-requisitos

- **Docker** + **Docker Compose** (`docker compose version` deve responder).
  No WSL2 + Windows, basta habilitar a integração no Docker Desktop em
  *Settings → Resources → WSL Integration*.
- Acesso de **root para editar `/etc/hosts`** (e o `hosts` do Windows se for usar o navegador no Windows).
- ~1 GB de espaço pra imagens.

## Subida da primeira vez

### 1. Configurar o domínio

O Caddy serve o app no domínio `texki2.local`. Aponte-o para `127.0.0.1` em ambos os lados (WSL + Windows, se aplicável):

```bash
# No WSL
echo "127.0.0.1 texki2.local" | sudo tee -a /etc/hosts
```

No Windows (somente se for abrir o navegador no host), edite `C:\Windows\System32\drivers\etc\hosts` como Administrador e adicione a mesma linha. Pelo WSL, dá pra abrir o Notepad elevado:

```bash
powershell.exe -Command "Start-Process notepad 'C:\Windows\System32\drivers\etc\hosts' -Verb RunAs"
```

### 2. Preencher o `.env`

```bash
cp .env.example .env
```

Troque **todos os `change-me`**:

- `POSTGRES_PASSWORD` — senha do Postgres
- `DATABASE_URL` — repita a mesma senha no formato `postgresql+psycopg://texki:<senha>@db:5432/texki2`
- `JWT_SECRET` — segredo longo e aleatório (`openssl rand -hex 48`)
- `SEED_ADMIN_PASSWORD` — senha do primeiro administrador

Para **produção**, troque também:

- `DOMAIN` — domínio real (ex.: `texki2.livreprint.com`)
- `ACME_EMAIL_OR_INTERNAL` — seu e-mail, para Let's Encrypt (em dev mantenha `internal`)

### 3. Subir a stack

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

### 4. Acessar

Abra `https://texki2.local` no navegador. Aceite o aviso do certificado interno do Caddy (só na primeira vez, em dev). Faça login com `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` do `.env`.

## Operação no dia-a-dia

### Após mudanças no código

A imagem traz o código embutido (`COPY . .`), então toda mudança precisa de rebuild:

```bash
docker compose up -d --build api    # ou web, ou ambos
```

### Migrations

```bash
# Aplicar todas as pendentes
docker compose exec api alembic upgrade head

# Criar uma nova
docker compose exec api alembic revision -m "nome curto da mudanca"

# Voltar uma revisão
docker compose exec api alembic downgrade -1
```

Schema **só** muda por migration. Nunca via `psql` direto.

### Testes

```bash
docker compose exec api pytest -q
```

### Logs

```bash
docker compose logs -f api
docker compose logs -f web
docker compose logs -f proxy
```

### Reset completo do banco (perde tudo)

```bash
docker compose down -v
docker compose up -d
docker compose exec api alembic upgrade head
docker compose exec api python -m app.db.seed
```

### Acesso direto ao Postgres

```bash
docker compose exec db psql -U texki -d texki2
```

## Convenções não-negociáveis

Detalhes em [CLAUDE.md](CLAUDE.md). Resumo:

- Dinheiro: sempre `Decimal` / `NUMERIC(10,2)` — nunca `float`.
- Erros: JSON `{ "error": { "code", "message", "details" } }` com HTTP correto.
- `created_at` / `updated_at` em UTC em todas as tabelas.
- RBAC é validado **na API** (fonte da verdade); o frontend só esconde o que o papel não usa.
- `item_pedido.preco_unitario` é **congelado** no momento do pedido.
- Regras de negócio em `backend/app/services/` — nunca dentro dos routers.

## Deploy

Em produção, na VPS:

```bash
./deploy.sh
```

Que faz `git pull` → `docker compose build` → `up -d` → `alembic upgrade head` → `python -m app.db.seed` (seed é idempotente).
