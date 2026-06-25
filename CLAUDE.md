# TEXKI2 — Contexto do Projeto

TEXKI2 é o sistema interno de controle de produção e administração de pedidos de DTF têxtil da Livreprint (reconstrução do "Texki"). Uso interno, ~10 usuários. Termos de domínio em PT-BR (cliente, pedido, impressão, orçamento, vendedora, impressor).

## Stack
- **Frontend:** Next.js (App Router) + TypeScript + Tailwind + shadcn/ui. UI simples e fácil de visualizar.
- **Backend:** FastAPI (Python). Regras de negócio ficam aqui.
- **Banco:** PostgreSQL. Schema só via migrations do **Alembic** (nunca alterar à mão).
- **Arquivos:** filesystem da VPS, sempre acessado pela camada `backend/app/storage/`.
- **Deploy:** Docker Compose numa VPS Ubuntu (serviços: web, api, db, proxy Caddy).

## Documentos (fonte da verdade — leia antes de implementar)
- `docs/PRD-TEXKI2.md` — requisitos (o quê).
- `docs/design-doc.md` — arquitetura, modelo de dados, fluxos (o como).
- `docs/minispec-RF5.md` — verificação de proporção da arte.
- `docs/roadmap-fatias.md` — ordem de construção das fatias.
- `docs/adr/` — decisões e seus porquês.

## Organização do código
- Monorepo: `backend/` (FastAPI) e `frontend/` (Next.js).
- Regras de negócio em `backend/app/services/` (`pricing`, `nesting`, `status`, `proportion`) — **nunca** dentro dos routers.
- Models em `models/`, schemas Pydantic em `schemas/`, routers por recurso em `api/`.

## Convenções não-negociáveis
- Dinheiro: sempre `Decimal` / `NUMERIC(10,2)` — nunca float.
- Erros: JSON `{ "error": { "code", "message", "details" } }` com HTTP correto.
- `created_at`/`updated_at` em UTC em todas as tabelas.
- RBAC é validado **na API** (fonte da verdade); o frontend só esconde o que o papel não usa.
- `item_pedido.preco_unitario` é **congelado** no momento do pedido (não recalcula com faixas futuras).

## Invariantes de domínio (fáceis de errar — detalhe no design doc)
- **Status do pedido:** recebido → pago → na fila de impressão → impressão pronta → pedido pronto → entregue. Cancelado sai do dashboard, mas fica na lista marcado como cancelado.
- **Status da impressão:** a imprimir → em andamento → concluída → cancelada.
- **Transições automáticas:** concluir impressão → pedidos vinculados viram "impressão pronta"; cancelar impressão → voltam para "pago". Devem ser **idempotentes**. Toda mudança de status/responsável vai para a **auditoria** (RNF3).
- **Preço por faixa:** vestuário por quantidade do item; DTF por metro por comprimento (design doc, Seção 4).
- **Proporção (RF5):** só PNG (com recorte da transparência), tolerância zero, cadeado estilo Photoshop. PDF/TIFF não checam.
- **Nesting (RF10):** largura útil 56 cm (bobina 57), margem 0,6 cm entre artes, rotação 90° permitida; comprimento total → faixa de preço do DTF. Não gera pedido.
- **Upload (RNF1):** PNG/PDF/TIFF, até 25 MB.

## Como trabalhar
- Leia os documentos acima antes de implementar.
- Trabalhe em **uma fatia por vez** (ver `docs/roadmap-fatias.md`). Antes de codar, mostre o plano.
- Commit por fatia, com mensagem que descreve a fatia.
- Se algo não estiver decidido, pergunte ou registre um ADR — não invente em silêncio.
