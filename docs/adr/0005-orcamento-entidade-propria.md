# ADR-0005 — Orçamento como entidade própria que não gera pedido

**Status:** aceito · **Data:** 2026-06-18

**Contexto.** A RF10 define um orçamento rápido de DTF (nesting de artes) usado durante o atendimento. Ele serve para passar um valor ao cliente, e não deve virar um pedido automaticamente.

**Decisão.** O Orçamento é uma entidade independente, que não cria Pedido. Produz o arranjo das artes + comprimento + valor total, e referencia o produto "DTF por metro" para precificação.

**Consequências.**
- (+) Desacopla o orçamento do fluxo de produção: é possível orçar sem comprometer a fila.
- (−) Se no futuro quiserem "converter um orçamento em pedido", isso será uma feature nova (não prevista agora).
