# Fatia 1 — Clientes (RF2) — Critérios de Aceite

**Story.** Como Vendedora (ou Administrador), quero cadastrar e gerenciar clientes, para registrar quem faz os pedidos e atender à LGPD.

## Escopo desta fatia
- **Inclui:** CRUD de clientes (criar, listar, ver, editar, excluir), campos de consentimento LGPD, e as permissões por papel.
- **Não inclui:** vínculo com pedidos (Fatia 3), busca/filtro avançado, importação.

## Campos
`primeiro_nome`, `ultimo_nome`, `endereco`, `telefone`, `consentimento_lgpd` (bool), `data_consentimento` (data) — além de `created_at`/`updated_at` automáticos (UTC).

Obrigatórios: `primeiro_nome` e `telefone`. 
Opcionais: `ultimo_nome` e `endereco`.

---

## Criar cliente
- **Given** uma usuária autenticada com papel Vendedora ou Administrador, **when** ela preenche `primeiro_nome` e `telefone` (e, opcionalmente, os demais campos) e salva, **then** o cliente é criado e passa a aparecer na lista.
- **Given** que o "consentimento LGPD" foi marcado, **when** salvo o cliente, **then** `data_consentimento` é gravada com a data atual.
- **Given** que o "consentimento LGPD" **não** foi marcado, **when** salvo o cliente, **then** `data_consentimento` fica vazia.
- **Given** que `primeiro_nome` ou `telefone` está em branco, **when** tento salvar, **then** recebo um erro de validação (HTTP 422, no formato de erro padrão) e o cliente **não** é criado.

## Listar clientes
- **Given** que existem clientes cadastrados, **when** abro a lista de clientes, **then** vejo cada cliente com, no mínimo, nome e telefone.
- **Given** que não há nenhum cliente, **when** abro a lista, **then** vejo um estado vazio claro (e não um erro).

## Ver e editar
- **Given** um cliente existente, **when** abro para editar, altero um campo e salvo, **then** a alteração persiste e aparece atualizada na lista.
- **Given** um cliente com consentimento marcado, **when** desmarco o consentimento e salvo, **then** `data_consentimento` é limpa.
- **Given** uma edição que deixa `primeiro_nome` ou `telefone` em branco, **when** tento salvar, **then** recebo erro de validação e a alteração inválida não é gravada.

## Excluir (direito ao esquecimento — LGPD)
- **Given** um cliente existente, **when** solicito a exclusão e confirmo, **then** o cliente é removido e seus dados saem do sistema.
- **Given** que cancelo a confirmação de exclusão, **when** volto, **then** o cliente continua intacto.

> **Nota (Fatia 3).** Como pedidos ainda não existem, a exclusão é direta. Quando houver pedidos vinculados a clientes, será preciso definir a regra (bloquear a exclusão, anonimizar o cliente, etc.). Registrar como decisão na época.

## Permissões
- **Given** uma usuária Vendedora ou Administrador, **when** acessa clientes, **then** consegue criar, listar, editar e excluir.
- **Given** um usuário Impressor, **when** tenta acessar clientes (pela interface ou diretamente pela API), **then** é bloqueado (HTTP 403 na API).
- **Given** uma requisição **não autenticada**, **when** chama qualquer endpoint de clientes, **then** recebe HTTP 401.

## Convenções (do design doc)
- Erros no formato padrão `{ "error": { "code", "message", "details" } }`.
- Validação no backend (fonte da verdade), espelhada no frontend para feedback rápido.
- `created_at`/`updated_at` em UTC.

---

## Definição de pronto
- [ ] Consigo criar, listar, editar e excluir clientes como Vendedora e como Administrador.
- [ ] Marcar consentimento grava a data; desmarcar limpa a data.
- [ ] Campos obrigatórios vazios são barrados com erro de validação no formato padrão.
- [ ] Impressor recebe 403 e requisição não autenticada recebe 401 nos endpoints de clientes.
- [ ] Existem testes passando cobrindo, no mínimo: criação válida, validação de campo obrigatório e bloqueio por papel.
