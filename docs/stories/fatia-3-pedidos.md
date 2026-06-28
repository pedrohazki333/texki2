# Fatia 3 — Pedidos (RF1 + RF5) — Critérios de Aceite

**Story.** Como Vendedora (ou Administrador), quero registrar pedidos com seus itens e artes, para que a produção tenha o pedido correto e o total calculado automaticamente.

## Escopo desta fatia
- **3a — Pedido + itens + total:** criar/ver/editar/excluir pedido, itens com preço pela faixa, total derivado.
- **3b — Artes + proporção:** anexar artes (upload via storage) e a verificação de proporção (RF5).
- **Não inclui:** separação por status no dashboard (Fatia 4), transições de status manuais/automáticas (Fatia 4/5) e o nesting do orçamento (Fatia 7). Aqui o pedido apenas **nasce em "recebido"**.

## Entidades e campos
- **Pedido:** `cliente` (FK), `vendedora`/responsável (FK), `status`, `total` (derivado), `data_entrega`; possui Itens e Artes.
- **Item de pedido:** `produto` (FK), `variacao` (FK, opcional), `quantidade`, `preco_unitario` (congelado), `subtotal` (derivado).
- **Arte:** `arquivo`, `largura_cm`, `altura_cm`, `observacoes`, `ordem`.

---

## 3a — Pedido, itens e total

### Criar pedido
- **Given** uma Vendedora autenticada, **when** seleciona um cliente, define `data_entrega`, adiciona ao menos um item e salva, **then** o pedido é criado com status `recebido`, `responsável` = a própria vendedora, e pode ser consultado.
- **Given** um pedido sem cliente, ou sem nenhum item, **when** tento salvar, **then** recebo erro de validação (422, formato padrão) e o pedido não é criado.
- **Given** um item cujo produto tem variações, **when** adiciono o item sem escolher a variação, **then** recebo erro de validação.
- **Given** um item com `quantidade` ausente ou ≤ 0, **when** salvo, **then** recebo erro de validação.

### Itens e preço (usa a lógica da Fatia 2)
- **Given** um item com produto e quantidade, **when** salvo, **then** o `preco_unitario` é calculado pela faixa aplicável (regra `min < medida <= max`) e **gravado/congelado** no item; `subtotal = quantidade × preco_unitario`.
- **Given** que as faixas de preço do produto mudam **depois**, **when** consulto um pedido já existente, **then** `preco_unitario` e `subtotal` permanecem os mesmos (congelados no momento do pedido).
- **Given** que edito a `quantidade` de um item, **when** salvo, **then** o `preco_unitario` é recalculado pela faixa correspondente à nova quantidade e regravado.
- **Given** um pedido com vários itens, **then** `total` = soma dos subtotais (derivado, nunca digitado à mão).

### Editar / excluir
- **Given** um pedido existente, **when** edito (itens, cliente, data) e salvo, **then** as alterações persistem e o total é recalculado.
- **Given** um pedido existente, **when** excluo e confirmo, **then** o pedido é removido.

### Permissões e responsável
- **Given** uma Vendedora ou Administrador, **when** cria/edita pedidos, **then** consegue.
- **Given** um Impressor, **when** tenta criar/editar um pedido (interface ou API), **then** é bloqueado (HTTP 403). *(A troca de status pelo Impressor é de outra fatia.)*
- **Given** uma requisição não autenticada, **then** HTTP 401.
- **Given** uma Vendedora, **when** tenta alterar o **responsável** do pedido para outra pessoa, **then** é bloqueada; **Given** um Administrador, **when** altera o responsável, **then** é permitido e o evento fica auditado (RNF3).

---

## 3b — Artes e verificação de proporção (RF5)

### Anexar artes
- **Given** um pedido, **when** anexo uma arte (arquivo + `largura_cm` + `altura_cm` + `observacoes`), **then** a arte fica vinculada ao pedido e o arquivo é salvo **pela camada de storage** (`backend/app/storage/`, ADR-0002).
- **Given** um arquivo fora de PNG/PDF/TIFF, ou maior que 25 MB, **when** tento subir, **then** recebo erro (RNF1) e nada é salvo.
- **Given** múltiplas artes no pedido, **then** a `ordem` é registrada (a primeira será a miniatura no dashboard da Fatia 4).

### Proporção (resumo — detalhes em `docs/minispec-RF5.md`)
- **Given** uma arte **PNG**, **when** o sistema a lê, **then** calcula a proporção **desconsiderando a transparência** (recorte do conteúdo).
- **Given** o cadeado fechado (padrão para PNG), **when** edito a largura ou a altura, **then** a outra medida é recalculada para manter a proporção exata — tolerância zero, ancorando na medida digitada primeiro (estilo cadeado do Photoshop).
- **Given** o cadeado aberto, **when** informo largura e altura, **then** a entrada é livre, sem correção.
- **Given** um arquivo **PDF ou TIFF**, **then** a verificação de proporção **não** é ativada e o cadeado inicia aberto para qualquer valor.

---

## Convenções (do design doc)
- Dinheiro sempre `Decimal`/`NUMERIC(10,2)`.
- Erros no formato padrão `{ "error": { "code", "message", "details" } }`.
- `created_at`/`updated_at` em UTC.
- Acesso a arquivos sempre pela camada de storage; RBAC validado na API.

---

## Notas e premissas
- **[Premissa — confirmar]** Um pedido exige **ao menos um item** para ser salvo.
- **[Premissa — confirmar]** Item de produto **DTF por metro** dentro de um pedido: a `quantidade` do item representa **metros**, e a faixa é selecionada por comprimento. *(Se, na prática, DTF por metro é vendido só via orçamento — Fatia 7 — então pedidos têm apenas itens de vestuário. Confirmar qual é o caso.)*
- **[Decisão pendente — herdada da Fatia 1]** Agora que pedidos referenciam clientes (e produtos), é preciso definir a exclusão de um cliente/produto com pedidos vinculados. **Proposta:** bloquear a exclusão direta; e, para o "esquecimento" LGPD de um cliente com pedidos, **anonimizar** os dados pessoais do cliente mantendo os registros de pedido. Confirmar antes de implementar a exclusão.

## Definição de pronto
- [x] Crio um pedido (cliente + responsável + ≥1 item + data de entrega) que nasce em `recebido`.
- [x] O `preco_unitario` de cada item vem da faixa correta e fica congelado; `subtotal` e `total` saem certos e derivados.
- [x] Editar a quantidade recalcula o preço; mudar as faixas depois não altera pedidos antigos.
- [x] Anexo artes (PNG/PDF/TIFF ≤ 25 MB) salvas pela camada de storage; tipo/tamanho inválidos são barrados.
- [x] A proporção funciona no PNG (recorte da transparência, cadeado, tolerância zero) e fica inativa em PDF/TIFF.
- [x] Impressor recebe 403, não autenticado recebe 401; só Admin troca o responsável (auditado).
- [x] Testes passando cobrindo, no mínimo: cálculo de total, congelamento de preço, validação de item e a regra de proporção do PNG.

## Decisões herdadas resolvidas
- **Pedido exige ≥ 1 item** (premissa confirmada).
- **DTF por metro entra em pedido**: a `quantidade` do item representa metros, e a faixa é escolhida por comprimento.
- **Exclusão com vínculos:** cliente com pedidos é bloqueado (409 `cliente.tem_pedidos`); para esquecimento LGPD oferece-se `POST /clientes/:id/anonimizar`. Produto com itens é bloqueado (409 `produto.tem_itens`) sem alternativa de anonimização.

## Notas de implementação
- Âncora do cadeado (RF5): adotada como "campo em edição" — quando a vendedora edita a largura, a altura é recalculada; e vice-versa. O backend aceita medidas que casem com a proporção por qualquer das duas como âncora, absorvendo o arredondamento de mm.
- Arredondamento das medidas corrigidas: **1 casa decimal** (mm), meio-acima.
