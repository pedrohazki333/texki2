# Fatia 2 — Produtos, variações e faixas de preço (RF3 + preços) — Critérios de Aceite

**Story.** Como Vendedora (ou Administrador), quero cadastrar produtos com suas variações e faixas de preço, para que o sistema calcule o preço correto nos pedidos (Fatia 3) e nos orçamentos (Fatia 7).

## Escopo desta fatia
- **Inclui:** CRUD de produtos; variações (cor/tamanho); faixas de preço; e a **lógica de seleção da faixa** (dado um produto e uma medida, retornar a faixa e o preço corretos).
- **Não inclui:** usar o preço dentro de pedidos (Fatia 3) e o nesting do orçamento (Fatia 7). Aqui se constrói a capacidade; o consumo vem depois.

## Entidades e campos
- **Produto:** `nome`, `tipo` (`dtf_por_metro` | `vestuario`).
- **Variação:** `cor`, `tamanho` — apenas para produtos de vestuário.
- **Faixa de preço:** `base` (`comprimento_m` | `quantidade`), `min`, `max` (nulo = aberto, sem teto), `preco_unitario` (`Decimal`/`NUMERIC(10,2)`).

## Convenção das faixas (limite)
Cada faixa cobre `min < medida <= max` — **limite inferior exclusivo, superior inclusivo**; `max` nulo significa "sem teto". Isso vale para os dois tipos de base e elimina ambiguidade nas bordas. Exemplos confirmados (design doc, Seção 4):

- **DTF por metro** (base `comprimento_m`): `(0,5] → 69,90` · `(5,10] → 59,90` · `(10,20] → 49,90` · `(20,∞) → 39,90`.
- **Vestuário** (base `quantidade`): `(0,10] → "1 a 10"` · `(10,50] → "11 a 50"` · `(50,∞) → "51+"`.

---

## Produtos (CRUD)
- **Given** uma usuária Vendedora ou Administrador, **when** cadastra um produto informando `nome` e `tipo` e salva, **then** o produto é criado e aparece na lista.
- **Given** um produto existente, **when** edito e salvo, **then** a alteração persiste.
- **Given** um produto existente, **when** excluo e confirmo, **then** o produto sai da lista.
- **Given** que `nome` ou `tipo` está em branco, **when** tento salvar, **then** recebo erro de validação (422, formato padrão) e o produto não é criado.

## Variações
- **Given** um produto do tipo `vestuario`, **when** adiciono uma variação com `cor` e `tamanho`, **then** a variação fica vinculada ao produto.
- **Given** um produto do tipo `dtf_por_metro`, **when** tento adicionar variação, **then** o sistema não permite (DTF por metro não tem variação).

## Faixas de preço
- **Given** um produto, **when** cadastro uma faixa com `base`, `min`, `max` e `preco_unitario`, **then** a faixa fica vinculada ao produto.
- **Given** um produto do tipo `dtf_por_metro`, **when** cadastro suas faixas, **then** a `base` deve ser `comprimento_m`; para `vestuario`, a `base` deve ser `quantidade`. Base incompatível com o tipo é rejeitada.
- **Given** que tento cadastrar uma faixa que **se sobrepõe** a outra do mesmo produto, **when** salvo, **then** recebo erro e a faixa não é criada (faixas não podem se sobrepor).
- **Given** `preco_unitario` ausente, negativo, ou `min`/`max` inconsistentes (`min >= max` com `max` não nulo), **when** salvo, **then** recebo erro de validação.

## Seleção de faixa (consulta de preço) — o coração da fatia
- **Given** um produto e uma medida (quantidade ou comprimento), **when** consulto o preço, **then** o sistema retorna a faixa aplicável e o `preco_unitario` dela, usando a regra `min < medida <= max`.
- **Given** um produto DTF e comprimento **5,00 m**, **then** retorna a faixa `(0,5]` → 69,90; com **5,01 m**, retorna `(5,10]` → 59,90.
- **Given** uma camiseta com quantidade **10**, **then** retorna `(0,10]` → 49,90; com **11**, retorna `(10,50]` → 39,90; com **51**, retorna `(50,∞)` → 29,90.
- **Given** uma medida que não cai em nenhuma faixa (lacuna na configuração), **when** consulto o preço, **then** recebo um **erro claro** — o sistema nunca "chuta" um preço.

## Permissões
- **Given** uma usuária Vendedora ou Administrador, **when** acessa produtos/variações/faixas, **then** consegue criar, listar, editar e excluir.
- **Given** um usuário Impressor, **when** tenta acessar (interface ou API), **then** é bloqueado (HTTP 403 na API).
- **Given** uma requisição não autenticada, **when** chama qualquer endpoint desta fatia, **then** recebe HTTP 401.

## Convenções (do design doc)
- Dinheiro sempre `Decimal`/`NUMERIC(10,2)` — nunca float.
- Erros no formato padrão `{ "error": { "code", "message", "details" } }`.
- `created_at`/`updated_at` em UTC.

---

## Notas
- **[Recomendado]** Pré-cadastrar via seed o catálogo conhecido — DTF por metro, Camiseta, Blusa de Moletom e Conjunto Moletom — com suas faixas (valores na Seção 4 do design doc). Isso deixa dados reais prontos para as Fatias 3 e 7. Se preferir cadastrar manualmente, tudo bem; é só uma conveniência.
- **Nota (Fatia 3).** Quando itens de pedido passarem a referenciar produtos/variações, será preciso definir a regra de exclusão de um produto já usado em pedidos (bloquear, inativar, etc.). Não trava nada agora; fica sinalizado.

## Definição de pronto
- [ ] Consigo cadastrar, editar e excluir produtos (com `tipo`) como Vendedora e Administrador.
- [ ] Produtos de vestuário aceitam variações; DTF por metro não.
- [ ] Consigo cadastrar faixas com base compatível com o tipo; sobreposição e dados inválidos são rejeitados.
- [ ] Dada uma medida, o sistema retorna a faixa e o preço corretos pela regra `min < medida <= max`, e dá erro claro se não houver faixa.
- [ ] Impressor recebe 403 e requisição não autenticada recebe 401.
- [ ] Existem testes passando cobrindo, no mínimo: seleção de faixa nas bordas (5,00 vs 5,01 m; 10 vs 11 un), rejeição de sobreposição e bloqueio por papel.
