# ADR-0003 — Relação Pedido ↔ Impressão (N–N) e transições automáticas de status

**Status:** aceito · **Data:** 2026-06-18

**Contexto.** Um pedido pode entrar em mais de uma impressão (reimpressão de parte que saiu errada). Concluir ou cancelar uma impressão precisa refletir no status dos pedidos vinculados.

**Decisão.** Modelar Pedido N–N Impressão por meio da tabela de junção `Pedido_Impressão`. Ao concluir uma impressão, os pedidos vinculados vão automaticamente para "impressão pronta"; ao cancelar, voltam para "pago". O status também pode ser alterado manualmente pelos papéis autorizados (Vendedora, Impressor, Administrador).

**Consequências.**
- (+) Suporta reimpressão sem duplicar pedidos.
- (+) Mantém o controle de produção consistente sem intervenção manual constante.
- (−) A transição automática precisa ser idempotente. **Detalhe resolvido no design doc (Seção 7.2):** quando um mesmo pedido está em duas impressões ao mesmo tempo, a última transição aplicada vale e o evento fica registrado na auditoria.
