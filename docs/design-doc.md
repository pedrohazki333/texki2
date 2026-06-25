# TEXKI2 — Design Doc

**Status:** pronto para desenvolvimento (v1.0) · **Autor:** Pedro Zelenski (com assistência) · **Data:** 2026-06-20

> O "como" técnico do TEXKI2. Complementa o PRD v1.2 (o "o quê") e os ADRs (as decisões). Itens marcados **[A confirmar]** ou **[Sugestão]** são propostas que dependem da sua validação. Documentos relacionados: `docs/PRD-TEXKI2.md`, `docs/minispec-RF5.md`, `docs/adr/`.

---

## 1. Visão geral da arquitetura

Três componentes principais, rodando numa VPS (Ubuntu 24.04) sob Docker Compose:

- **Frontend** — Next.js (App Router) + TypeScript + Tailwind + shadcn/ui. Interface enxuta e fácil de visualizar.
- **Backend** — FastAPI (Python), expondo uma API REST em JSON. Concentra as regras de negócio.
- **Banco** — PostgreSQL.
- **Proxy reverso** — Caddy, para HTTPS automático e roteamento (`/` → frontend, `/api` → backend).
- **Arquivos** — armazenados no sistema de arquivos da VPS (ver Seção 8 e ADR-0002).

```
Navegador
   │  HTTPS
   ▼
 Caddy (proxy)
   ├── /        → Frontend (Next.js)
   └── /api/*   → Backend (FastAPI) ── PostgreSQL
                                    └── Arquivos (filesystem da VPS)
```

O backend é a **fonte da verdade** das regras (preço, status, proporção, nesting, permissões). O frontend nunca decide nada sensível sozinho; ele chama a API.

---

## 2. Estrutura do repositório

Monorepo único, com front e back separados em pastas de primeiro nível. Organização por domínio para manter o código limpo e escalável.

```
texki2/
├── CLAUDE.md                 # memória curta lida pelo Claude Code
├── docker-compose.yml
├── .env.example
├── deploy.sh
├── docs/
│   ├── PRD-TEXKI2.md
│   ├── design-doc.md
│   ├── minispec-RF5.md
│   └── adr/
├── backend/                  # FastAPI
│   ├── app/
│   │   ├── main.py
│   │   ├── core/             # config, segurança, sessão de banco
│   │   ├── models/           # modelos SQLAlchemy (tabelas)
│   │   ├── schemas/          # schemas Pydantic (entrada/saída)
│   │   ├── api/              # routers por recurso (auth, clientes, pedidos…)
│   │   ├── services/         # regras de negócio (pricing, nesting, status, proporção)
│   │   ├── storage/          # abstração de arquivos (ADR-0002)
│   │   └── db/               # migrations (Alembic) + seed
│   ├── tests/
│   ├── pyproject.toml
│   └── Dockerfile
└── frontend/                 # Next.js + TS + Tailwind + shadcn/ui
    ├── app/                  # rotas (App Router)
    ├── components/           # ui (shadcn) + componentes de domínio
    ├── lib/                  # cliente da API, helpers
    ├── hooks/
    ├── package.json
    └── Dockerfile
```

**Princípio de organização:** as regras de negócio ficam em `backend/app/services/` (ex.: `pricing.py`, `nesting.py`, `status.py`, `proportion.py`), nunca dentro dos routers. Isso mantém a lógica testável e o código fácil de crescer.

---

## 3. Modelo de dados

Tipos: dinheiro em `NUMERIC(10,2)` (nunca float); chaves primárias `BIGSERIAL`; todas as tabelas com `created_at`/`updated_at` em UTC. Índices nas chaves estrangeiras, em `usuario.email` (único) e em `pedido.status` (filtro do dashboard).

### Entidades

| Entidade | Campos principais |
|---|---|
| **usuario** | id, email (único), senha_hash, nome, role (`vendedora`\|`impressor`\|`administrador`), ativo |
| **cliente** | id, primeiro_nome, ultimo_nome, endereco, telefone, consentimento_lgpd (bool), data_consentimento |
| **produto** | id, nome, tipo (`dtf_por_metro`\|`vestuario`) |
| **variacao** | id, produto_id (FK), cor, tamanho — apenas para vestuário |
| **faixa_preco** | id, produto_id (FK), base (`comprimento_m`\|`quantidade`), min, max (nulo = aberto), preco_unitario |
| **pedido** | id, cliente_id (FK), vendedora_id (FK, responsável), status (enum), total (derivado), data_entrega |
| **item_pedido** | id, pedido_id (FK), produto_id (FK), variacao_id (FK, nulo), quantidade, preco_unitario (congelado), subtotal (derivado) |
| **arte** | id, pedido_id (FK), arquivo_path, largura_cm, altura_cm, observacoes, ordem |
| **impressao** | id, comprimento_cm, status (enum), observacoes, impressor_id (FK) |
| **pedido_impressao** | pedido_id (FK), impressao_id (FK) — junção N–N |
| **orcamento** | id, vendedora_id (FK), produto_dtf_id (FK), largura_util_cm (56), comprimento_total_cm (derivado), valor_total (derivado) |
| **arte_orcamento** | id, orcamento_id (FK), arquivo_path, quantidade, largura_cm, altura_cm |
| **auditoria** | id, usuario_id, entidade, entidade_id, campo, valor_anterior, valor_novo, timestamp |

### Enums

- `usuario.role`: `vendedora` · `impressor` · `administrador`
- `pedido.status`: `recebido` · `pago` · `na_fila_de_impressao` · `impressao_pronta` · `pedido_pronto` · `entregue` · `cancelado`
- `impressao.status`: `a_imprimir` · `em_andamento` · `concluida` · `cancelada`

### Relações

cliente 1–N pedido · usuario(vendedora) 1–N pedido · pedido 1–N item_pedido · item_pedido N–1 produto/variação · pedido 1–N arte · produto 1–N variacao · produto 1–N faixa_preco · impressor 1–N impressao · **pedido N–N impressao** (via pedido_impressao) · vendedora 1–N orcamento · orcamento 1–N arte_orcamento · orcamento N–1 produto (DTF por metro).

### Observação sobre `preco_unitario` congelado

No `item_pedido`, o `preco_unitario` é **gravado no momento do pedido** (cópia da faixa aplicável). Assim, alterar uma faixa de preço no futuro não muda o valor de pedidos antigos.

---

## 4. Preços e faixas (regras)

A precificação é por **faixa**. Cada produto tem faixas; a faixa é escolhida por uma medida (comprimento em metros para DTF, quantidade em unidades para vestuário), e o `preco_unitario` da faixa é a tarifa por unidade dessa medida.

`subtotal = medida × preco_unitario_da_faixa`

### DTF por metro (confirmado — usado na RF10)

| Comprimento total | R$/m |
|---|---|
| até 5 m | 69,90 |
| acima de 5 e até 10 m | 59,90 |
| acima de 10 e até 20 m | 49,90 |
| acima de 20 m | 39,90 |

As faixas são contíguas e cobrem todo o intervalo (as lacunas da tabela original — 9–10 m e 19–20 m — foram fechadas conforme acima).

### Vestuário — por quantidade (confirmado)

Camiseta, Blusa de Moletom e Conjunto Moletom têm preço por faixa de quantidade (estende a RF3, que previa preço único). As faixas se aplicam ao preço de cada **item do pedido** (RF1), pela quantidade daquele item:

| Produto | 1 a 10 un. | 11 a 50 un. | acima de 50 un. |
|---|---|---|---|
| Camiseta | 49,90 | 39,90 | 29,90 |
| Blusa de Moletom | 99,90 | 89,90 | 79,90 |
| Conjunto Moletom | 149,90 | 139,90 | 129,90 |

A faixa é escolhida pela quantidade do próprio item: ex., 15 camisetas caem em "11 a 50 un." → 39,90/unidade.

---

## 5. Autenticação e autorização (RBAC)

- **Login:** e-mail + senha. Não há auto-cadastro; o administrador cria os usuários (RF8).
- **Senhas:** armazenadas com hash forte (bcrypt ou argon2). Nunca em texto puro.
- **Sessão:** token JWT entregue em **cookie httpOnly** (mitiga roubo por script no navegador), com expiração curta + renovação. **[Sugestão]**
- **RBAC:** cada endpoint declara o papel exigido, validado por uma dependência no FastAPI. A API é a fonte da verdade; o frontend apenas esconde o que o papel não usa (conveniência visual, não segurança).
- **Primeiro administrador:** criado por um script de seed na primeira subida.

A matriz de permissões da Seção 7 do PRD é o contrato a ser implementado aqui.

---

## 6. Padrões transversais

- **Validação:** Pydantic no backend; validação espelhada no frontend (ex.: zod) para feedback rápido.
- **Erros:** formato JSON consistente — `{ "error": { "code": "...", "message": "...", "details": [...] } }` — com códigos HTTP corretos (400/401/403/404/409/422).
- **Dinheiro:** sempre `Decimal` / `NUMERIC(10,2)`.
- **Auditoria (RNF3):** toda mudança de `status` e de `responsável` de pedido grava uma linha em `auditoria` (quem, o quê, quando).
- **Migrations:** Alembic. O schema **nunca** é alterado à mão no banco — sempre por migration versionada.
- **Testes:** pytest no backend, com foco na lógica de negócio crítica — **pricing, nesting, transições de status e verificação de proporção**. No frontend, testes nos fluxos-chave. Não se busca cobertura total; busca-se cobrir o que quebra silencioso.
- **Estilo de código:** ruff + black (Python); eslint + prettier e TypeScript em modo estrito (frontend).

---

## 7. Fluxos-chave

### 7.1 Criação de pedido e cálculo de total
1. Vendedora seleciona cliente, adiciona itens (produto + variação + quantidade) e anexa artes.
2. Para cada item, o backend escolhe a faixa de preço pela medida e calcula `subtotal`; `total = Σ subtotais`.
3. Ao anexar arte PNG, roda a verificação de proporção (ver `minispec-RF5.md`).
4. Pedido nasce em `recebido`.

### 7.2 Transições automáticas de status (ver ADR-0003)
- **Concluir impressão** → todos os pedidos vinculados vão para `impressao_pronta`.
- **Cancelar impressão** → os pedidos vinculados voltam para `pago`.
- Mudança manual de status permitida a Vendedora, Impressor e Administrador.
- Quando um pedido está em duas impressões ao mesmo tempo (uma conclui, outra é cancelada): a última transição aplicada vale, e o evento fica registrado na auditoria. As transições automáticas devem ser idempotentes. *(Regra padrão adotada; revisável caso a operação real peça outro comportamento.)*

### 7.3 Orçamento de DTF — nesting (RF10)
1. Vendedora sobe artes (PNG, fundo removido) com quantidade e dimensões (largura/altura cm).
2. **Empacotamento:** as artes são arranjadas numa faixa de **largura útil 56 cm** (bobina 57 cm, ~0,5 cm de cada lado), com **margem obrigatória de 0,6 cm entre artes**, e **rotação de 90° permitida** para melhor aproveitamento. O objetivo é minimizar o comprimento total.
   - Técnica: problema de *strip packing* (faixa de largura fixa, minimizar comprimento). Recomenda-se uma heurística de empacotamento com rotação (ex.: biblioteca `rectpack`), inflando cada arte pela margem antes de empacotar. Otimização exata é desnecessária para o volume de artes por orçamento.
3. **Comprimento total** do arranjo → seleciona a faixa de preço do DTF (Seção 4) → `valor_total = comprimento_m × R$/m`.
4. O sistema exibe uma **visualização do arranjo** (retângulos posicionados) + o valor total. O orçamento **não gera pedido** (ADR-0005).

### 7.4 Verificação de proporção (RF5)
Detalhada em `docs/minispec-RF5.md`. Resumo: leitura só de PNG (com recorte da transparência), tolerância zero, cadeado de proporção (estilo Photoshop), correção ancorada na medida digitada primeiro.

---

## 8. Armazenamento de arquivos (ADR-0002)

- Artes de pedido e PNGs de orçamento ficam no **filesystem da VPS**, num diretório dedicado (ex.: `/srv/texki2/uploads`), montado como volume no container do backend.
- Todo acesso a arquivo passa por **uma única camada** (`backend/app/storage/`) com operações `salvar/obter/remover`. Isso isola o sistema do meio de armazenamento e permite trocar por storage de objetos no futuro sem espalhar mudanças.
- **Validação no upload (RNF1):** tipo em PNG/PDF/TIFF e tamanho ≤ 25 MB. Nome físico por UUID, preservando a extensão.

---

## 9. Ambiente, deploy e backup

Você usa uma VPS Ubuntu 24.04 e faz deploy/banco manualmente pelo terminal — o que funciona. A proposta abaixo mantém o controle pelo terminal, mas torna o processo **reprodutível** (mesma configuração toda vez), que é o ganho "profissional" sem complexidade desnecessária.

### Docker Compose
Definir os serviços num `docker-compose.yml`: `web` (Next.js), `api` (FastAPI via uvicorn/gunicorn), `db` (PostgreSQL com volume nomeado), `proxy` (Caddy). Os uploads entram como volume apontando para `/srv/texki2/uploads`. Subir tudo com um comando: `docker compose up -d`.

### Fluxo de deploy (manual, reprodutível) — `deploy.sh`
1. `git pull` no servidor.
2. `docker compose build`.
3. `docker compose up -d`.
4. `docker compose exec api alembic upgrade head` (aplica migrations).

### Configuração
- Segredos (credenciais do banco, segredo do JWT) num arquivo `.env` no servidor, **fora do git** (`.env.example` versionado como modelo).

### Backup (RNF5)
- Cron diário: `pg_dump` do banco + `tar` do diretório de uploads, com retenção (ex.: 7 dias) e cópia para fora da VPS quando possível.

### Futuro (não obrigatório agora)
- CI/CD (ex.: GitHub Actions) para automatizar build/deploy quando o projeto amadurecer. Por ora, o `deploy.sh` manual é suficiente.

---

## 10. Itens menores em aberto

As decisões estruturais estão fechadas. Restam apenas detalhes de implementação que **não bloqueiam** o início do desenvolvimento:

1. **Pedido em duas impressões simultâneas** — regra padrão adotada na Seção 7.2; reavaliar só se a operação real exigir outro comportamento.
2. **Mini-spec da RF5** — dois micro-detalhes (comportamento da âncora e arredondamento da medida) marcados em `docs/minispec-RF5.md`; podem ser definidos na hora de implementar a RF5.
