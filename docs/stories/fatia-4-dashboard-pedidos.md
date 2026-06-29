# Fatia 4 — Dashboard de pedidos (RF6) + auditoria — Critérios de Aceite

**Story.** Como Vendedora, Impressor ou Administrador, quero ver os pedidos organizados por status e trocar o status deles, para acompanhar e tocar a produção.

## Escopo desta fatia
- **Inclui:** o dashboard de pedidos (lista por status, ordenada por data, com miniatura da primeira arte), a **mudança manual** de status, e o registro em **auditoria** (RNF3).
- **Não inclui:** as **transições automáticas** de status disparadas por impressões (Fatia 5) e o dashboard de impressões (Fatia 6).

---

## Dashboard (visão por status)
- **Given** pedidos em vários status, **when** abro o dashboard, **then** vejo os pedidos separados por status (`recebido`, `pago`, `na fila de impressão`, `impressão pronta`, `pedido pronto`, `entregue`), e dentro de cada status ordenados por data de registro.
- **Given** um pedido com artes, **when** vejo seu card, **then** ele exibe a **primeira arte** (a de menor `ordem`) como miniatura.
- **Given** um pedido **sem** arte, **when** vejo seu card, **then** exibe um placeholder, sem quebrar o layout.
- **Given** um pedido com status `cancelado`, **when** olho o dashboard, **then** ele **não** aparece ali.

## Lista completa e cancelados
- **Given** pedidos incluindo cancelados, **when** abro a lista completa de pedidos, **then** vejo todos — inclusive os cancelados, claramente marcados como tal.

## Mudança manual de status
- **Given** uma usuária Vendedora, Impressor ou Administrador, **when** altera o status de um pedido pelo dashboard, **then** o status é atualizado e o pedido passa a aparecer no grupo correspondente.
- **Given** que defino o status de um pedido como `cancelado`, **then** ele sai do dashboard, mas permanece na lista completa marcado como cancelado.
- **Given** um Impressor, **when** muda o status de um pedido, **then** é permitido (a troca de status é liberada aos três papéis — diferente do CRUD de pedidos da Fatia 3).

## Auditoria (RNF3)
- **Given** uma mudança de status, **when** ela ocorre, **then** é registrada na auditoria: quem alterou, qual pedido, status anterior, status novo e quando (UTC).
- **Given** um pedido, **when** consulto seu histórico, **then** vejo as mudanças de status registradas.

## Desempenho e miniaturas (RNF4)
- **Given** muitos pedidos com artes anexadas, **when** abro o dashboard, **then** as miniaturas são versões **otimizadas/redimensionadas** — nunca o arquivo cheio de até 25 MB — e o carregamento fica dentro do alvo **P95 < 1,5 s**.

## Permissões
- **Given** uma usuária Vendedora, Impressor ou Administrador autenticada, **when** acessa o dashboard e troca status, **then** consegue.
- **Given** uma requisição não autenticada, **when** chama os endpoints do dashboard/status, **then** recebe HTTP 401.

## Convenções (do design doc)
- Erros no formato padrão `{ "error": { "code", "message", "details" } }`.
- `created_at`/`updated_at` e timestamps de auditoria em UTC.
- Miniaturas geradas/servidas pela camada de storage; RBAC validado na API.

---

## Notas e premissas
- **[Premissa — confirmar]** A mudança manual permite definir **qualquer status** do ciclo (inclusive voltar atrás), conforme o "deliberadamente" do PRD. Se quiser restringir as transições (ex.: proibir pular etapas), é uma regra a adicionar.
- **Miniaturas:** atender ao RNF4 implica **gerar uma versão reduzida** da primeira arte. Recomendação: gerar a miniatura no momento do upload (Fatia 3) e guardá-la via storage, ou gerar sob demanda com cache. Decisão de implementação — registrar se relevante.
- As **transições automáticas** (concluir/cancelar impressão → status do pedido) chegam na Fatia 5; aqui só existe a troca manual.

## Definição de pronto
- [ ] Vejo os pedidos separados por status, ordenados por data, com a primeira arte como miniatura (e placeholder quando não há arte).
- [ ] Pedidos cancelados somem do dashboard, mas continuam na lista completa marcados como cancelados.
- [ ] Vendedora, Impressor e Administrador trocam o status pelo dashboard; cada troca fica auditada (quem, antes→depois, quando).
- [ ] As miniaturas são otimizadas e o dashboard carrega dentro do alvo de desempenho.
- [ ] Requisição não autenticada recebe 401.
- [ ] Testes passando cobrindo, no mínimo: agrupamento por status, ocultação de cancelados no dashboard, registro de auditoria na troca de status e uso de miniatura otimizada.
