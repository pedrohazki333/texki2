# TEXKI2 — Roadmap de fatias (proposta)

Ordem de construção em **fatias verticais finas** — cada uma ponta a ponta (banco → API → tela) — na **ordem de dependência**, não na numeração dos RFs. Por fatia: escrever os critérios de aceite (a "definição de pronto") → plan mode → implementar → testar → commit.

---

## Fatia 0 — Fundação + Autenticação (esqueleto)
A integração mais arriscada primeiro, para provar a stack costurada cedo.
- Scaffolding: backend (FastAPI), frontend (Next.js), `docker-compose` (web, api, db, proxy), Alembic, conexão com o PostgreSQL.
- Usuário + login (e-mail + senha, cookie httpOnly) + dependência de RBAC + seed do primeiro administrador.
- Shell mínimo do dashboard protegido por login.
- **Pronto quando:** subo tudo com `docker compose`, faço login como admin e vejo uma tela protegida.

## Fatia 1 — Clientes (RF2)
CRUD mais simples e independente; estabelece o padrão de CRUD ponta a ponta para as próximas.
- Inclui consentimento LGPD + data do consentimento.
- **Pronto quando:** cadastro, edito, listo e excluo clientes.

## Fatia 2 — Produtos, variações e faixas de preço (RF3 + preços)
Necessária antes de pedidos e orçamento.
- Produto (tipo `dtf_por_metro`/`vestuario`), variações (cor/tamanho), faixas de preço.
- Lógica de seleção da faixa correta (design doc, Seção 4).
- **Pronto quando:** cadastro produtos com variações e faixas, e o sistema escolhe a faixa certa pela quantidade/comprimento.

## Fatia 3 — Pedidos (RF1 + RF5) — núcleo do sistema
Depende de Clientes e Produtos. Sugiro dividir em duas:
- **3a — Pedido + itens + total:** criação do pedido com itens, cálculo de subtotal/total via faixas. *Pronto quando:* crio um pedido com itens e o total sai correto.
- **3b — Artes + proporção:** upload de artes (via camada de storage) + verificação de proporção (RF5). *Pronto quando:* anexo um PNG, o cadeado de proporção funciona e o arquivo é salvo.

## Fatia 4 — Dashboard de pedidos (RF6) + auditoria
Depende de Pedido/Arte.
- Lista por status, ordenada por data, com miniatura da primeira arte; mudança manual de status; registro em auditoria (RNF3).
- **Pronto quando:** vejo os pedidos separados por status com miniatura e troco o status (e a mudança fica auditada).

## Fatia 5 — Impressões (RF4) + vínculo N–N + transições automáticas
Depende de Pedido.
- Impressão (status a imprimir → … → cancelada), vínculo N–N com pedidos, regras automáticas (concluir → "impressão pronta"; cancelar → "pago"), idempotentes e auditadas.
- **Pronto quando:** crio uma impressão com pedidos, concluo e os pedidos viram "impressão pronta"; cancelo e voltam para "pago".

## Fatia 6 — Dashboard de impressões (RF7)
Depende de Impressão.
- Lista de impressões por status, ordenada por data.
- **Pronto quando:** vejo as impressões separadas por status.

## Fatia 7 — Orçamento / nesting (RF10)
Depende de Produtos (faixas do DTF). **Independente de Pedidos.**
- Upload de PNGs (quantidade + dimensões), empacotamento (56 cm úteis, margem 0,6 cm, rotação 90°), comprimento total → preço, visualização do arranjo. Não gera pedido.
- **Pronto quando:** subo artes e recebo o arranjo desenhado + comprimento total + valor.

## Fatia 8 — Administração de usuários (RF8)
Depende da autenticação (Fatia 0). O seed já cobre o bootstrap, então isto não bloqueia nada antes.
- Admin adiciona, exclui e altera o papel dos usuários.
- **Pronto quando:** como admin, crio um usuário com papel e ele consegue logar.

## Fatia 9 — Relatórios (RF9)
Por último: depende de dados de pedidos e impressões já existirem.
- Relatório de vendas e de impressões.

---

## Observações sobre a ordem
- A fatia mais complexa é a **7 (nesting)**. Se preferir de-riscar o algoritmo cedo, pode movê-la para logo após a Fatia 2 (ela só depende dos produtos).
- A **8 (admin de usuários)** pode subir para logo após a Fatia 0, se for conveniente — não há dependência forte.
- Antes de cada fatia, escreva os **critérios de aceite** (Given/When/Then). É o que o Claude Code usa para saber que terminou e o que você usa para aceitar ou rejeitar.
