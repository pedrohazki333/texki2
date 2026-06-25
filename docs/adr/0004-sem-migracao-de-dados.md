# ADR-0004 — Sem migração de dados do Texki

**Status:** aceito · **Data:** 2026-06-18

**Contexto.** O Texki atual contém muitas inconsistências, e a principal base de clientes da loja não reside nele.

**Decisão.** Não migrar dados do Texki. O TEXKI2 inicia com base vazia.

**Consequências.**
- (+) Evita carregar inconsistências para o sistema novo.
- (+) Simplifica o lançamento (sem script de migração nem validação de dados legados).
- (−) Produtos e clientes recorrentes precisarão ser cadastrados manualmente no início; não haverá histórico importado.
