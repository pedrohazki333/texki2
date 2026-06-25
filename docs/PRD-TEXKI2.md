# PRD — TEXKI2

**Status:** definitivo (pronto para desenvolvimento) · **Autor:** Pedro Zelenski · **Data:** 2026-06-18 · **Versão:** 1.2

> **Versão 1.2 — definitiva.** Consolida todas as decisões das revisões anteriores. Não há mais questões em aberto: a última pendência (migração de dados) foi resolvida e o documento está fechado para desenvolvimento.

Documentos relacionados: `docs/design-doc.md`, `docs/minispec-RF5.md`, `docs/adr/`.

---

## Sumário

1. Contexto
2. Problema e Justificativa
3. Usuários (Personas)
4. Requisitos Funcionais
5. Modelo de Status (Pedido e Impressão)
6. Requisitos Não-Funcionais
7. Permissões por Papel
8. Modelo de Dados
9. Stack do Projeto

---

## 1. Contexto

TEXKI2 é a reconstrução do Texki, sistema interno de controle de produção e administração de pedidos de DTF (Direct to Film) têxtil já em uso na empresa (atualmente em Laravel + Blade, CRUD em produção). O objetivo é melhorar o que existe, não recomeçar do zero conceitualmente.

A stack será completamente substituída por uma base mais escalável e moderna, definida na Seção 9.

Não haverá migração de dados do Texki para o TEXKI2: a base atual contém muitas inconsistências e a principal base de clientes da loja não reside nela. O TEXKI2 inicia com base vazia.

## 2. Problema e Justificativa

Empresas que vendem produtos de DTF têxtil sofrem para administrar pedidos e controlar a produção. Gasta-se muito tempo no atendimento e na parametrização do pedido, há dificuldade de registrar cada pedido de forma organizada e, como consequência, o controle de produção trava.

**Dores do Texki atual.** Ausência de travas e validações no momento do cadastro do pedido — o que permite o registro de pedidos inconsistentes — e falta de escalabilidade do sistema antigo. O foco da v2 é garantir o cadastro correto dos pedidos e a troca confiável de status, que é do que o controle de produção depende.

## 3. Usuários (Personas)

| Papel | Qtd. | Responsabilidades |
|---|---|---|
| Vendedora | ~6 | Registra pedidos e atualiza status, faz orçamentos, cadastra clientes, acessa o dashboard. |
| Impressor | 1 | Registra e administra impressões, acessa o dashboard. |
| Administrador | 3 | Acessa relatórios e dashboard, gerencia usuários. |

**Regra.** A administração de impressões é restrita ao papel Impressor (além do Administrador). Não se trata de gargalo operacional, e sim de uma regra de acesso.

## 4. Requisitos Funcionais

- **RF1 — CRUD de pedidos DTF.** Campos: itens (preço unitário, quantidade, subtotal), artes (largura, altura, observações), cliente, vendedora (responsável), status, total, data de entrega. O campo total é derivado da soma dos subtotais dos itens (não digitado manualmente). Acesso: papel Vendedora.
- **RF2 — CRUD de clientes.** Campos: primeiro nome, último nome, endereço, telefone, consentimento LGPD (booleano) e data do consentimento. Acesso: papel Vendedora.
- **RF3 — CRUD de produtos (itens dos pedidos).** Campos: nome, variação (cor, tamanho), preço. São produtos personalizáveis da loja, geralmente camisetas ou moletons. A maioria tem variação, mas alguns não (ex.: "DTF por metro (até 5m)"). Acesso: papel Vendedora.
- **RF4 — CRUD de impressões.** Campos: comprimento da impressão, pedidos vinculados, status, observações, responsável (impressor). Status da impressão: a imprimir → em andamento → concluída → cancelada. Acesso: papel Impressor.
- **RF5 — Verificação da proporção da arte.** Ao anexar a arte (ou artes) no pedido, o sistema lê as dimensões em pixels e calcula a proporção; ao informar largura/altura de impressão, compara as proporções e impede/avisa se divergirem, evitando medidas incorretas. A leitura deve desconsiderar os espaços em branco de um PNG com fundo removido para calcular a proporção correta da arte. (Detalhado em `docs/minispec-RF5.md`.)
- **RF6 — Dashboard de pedidos.** Lista de pedidos separada por status e ordenada por data de registro. Cada pedido exibe a primeira arte anexada como miniatura, para facilitar a localização visual. O status dos pedidos pode ser atualizado deliberadamente pelos papéis autorizados, conforme a Seção 5. Acesso: papéis Vendedora e Impressor.
- **RF7 — Dashboard de impressões.** Lista de impressões no dashboard, separada por status e ordenada por data, seguindo os mesmos princípios de organização da lista de pedidos. Acesso: papel Impressor (e Administrador).
- **RF8 — Administração de usuários.** O administrador adiciona, exclui e altera o papel (role) de usuários. Acesso: papel Administrador.
- **RF9 — Relatórios.** Página de geração de relatório de vendas e de impressões. Acesso: papel Administrador.
- **RF10 — Orçamento rápido de DTF (nesting de artes).** Voltado a orçamentos somente de DTF (sem produtos personalizados). A vendedora sobe as artes em PNG com fundo removido, informando a quantidade e as dimensões de cada uma. O sistema arranja (nesting) as artes dentro de uma largura útil de 56 cm — a bobina é de 57 cm e 1 cm é reservado como margem lateral — e calcula o comprimento total do arranjo. O valor é calculado por metro linear conforme o produto "DTF por metro" aplicável (ex.: arranjo de 2,65 m → R$ 69,90/m do produto "DTF Por metro até 5m"). O sistema exibe uma visualização do arranjo e o valor total para a vendedora repassar ao cliente. O orçamento não gera pedido. Acesso: papel Vendedora.
  - *Detalhes resolvidos no design doc:* rotação de 90° permitida; margem obrigatória de 0,6 cm entre artes; faixas de preço por comprimento definidas. Ver `docs/design-doc.md`, Seções 4 e 7.3.

## 5. Modelo de Status (Pedido e Impressão)

### 5.1. Status do pedido

**recebido → pago → na fila de impressão → impressão pronta → pedido pronto → entregue**

- **Atualização manual:** o status pode ser alterado deliberadamente por qualquer usuário com papel Vendedora, pelo Impressor e pelo Administrador, a partir do dashboard.
- **Atualização automática (impressão concluída):** ao concluir uma impressão, os pedidos vinculados àquele trabalho são automaticamente movidos para "impressão pronta".
- **Atualização automática (impressão cancelada):** se uma impressão é cancelada, os pedidos vinculados voltam automaticamente para o status "pago".
- **Cancelamento do pedido:** um pedido cancelado sai do dashboard, mas permanece normalmente na lista de pedidos, marcado como cancelado.

### 5.2. Status da impressão

**a imprimir → em andamento → concluída → cancelada**

## 6. Requisitos Não-Funcionais

- **RNF1 — Tamanho de arquivo de arte.** Suportar arquivos de até 25 MB nos formatos aceitos: PNG, PDF e TIFF.
- **RNF2 — LGPD.** Dados de cliente devem ser armazenados conforme a LGPD (consentimento + exclusão sob demanda).
- **RNF3 — Auditoria.** Registrar quem alterou status/responsável de cada pedido e quando (evita conflito entre setores de produção).
- **RNF4 — Desempenho do dashboard.** Tempo-alvo de carregamento da lista de pedidos, que renderiza miniaturas de arte: P95 < 1,5 s.
- **RNF5 — Backup e retenção.** Política de backup do banco de dados e dos arquivos de arte (armazenados no servidor de hospedagem), com periodicidade e retenção definidas.

## 7. Permissões por Papel

| Funcionalidade | Vendedora | Impressor | Admin. |
|---|---|---|---|
| CRUD de pedidos (RF1) | Sim | — | Sim |
| Alterar responsável de um pedido | — | — | Sim |
| Atualizar status do pedido (Seção 5) | Sim | Sim | Sim |
| CRUD de clientes (RF2) | Sim | — | Sim |
| CRUD de produtos (RF3) | Sim | — | Sim |
| CRUD de impressões (RF4) | — | Sim | Sim |
| Dashboard de pedidos (RF6) | Sim | Sim | Sim |
| Dashboard de impressões (RF7) | — | Sim | Sim |
| Orçamento rápido de DTF (RF10) | Sim | — | Sim |
| Administração de usuários (RF8) | — | — | Sim |
| Relatórios (RF9) | — | — | Sim |

## 8. Modelo de Dados

| Entidade | Campos / relações |
|---|---|
| Cliente | primeiro_nome, ultimo_nome, endereco, telefone, consentimento_lgpd (bool), data_consentimento |
| Produto | nome, preco; possui Variações (cor, tamanho) — alguns produtos não têm variação |
| Pedido | cliente (FK), vendedora/responsável (FK), status, total (derivado), data_entrega; possui Itens e Artes |
| Item | preco_unitario, quantidade, subtotal; referencia Produto/Variação |
| Arte | largura, altura, observacoes, arquivo_imagem (armazenado no servidor de hospedagem) |
| Impressão | comprimento, status, observacoes, responsável (FK Impressor) |
| Pedido_Impressão | tabela de junção (N–N): vincula Pedidos a Impressões e suporta reimpressões |
| Orçamento | vendedora (FK), produto_dtf (FK, para precificação), largura_util (56 cm), comprimento_total (derivado), valor_total (derivado), data; não gera Pedido; possui Artes de orçamento |
| Arte de Orçamento | arquivo_png (fundo removido), quantidade, largura, altura |
| Usuário | role (Vendedora \| Impressor \| Administrador) |

**Relações principais:** Cliente 1–N Pedido · Vendedora 1–N Pedido · Pedido 1–N Item · Item N–1 Produto/Variação · Pedido 1–N Arte · Produto 1–N Variação · Impressor 1–N Impressão · Pedido N–N Impressão (via Pedido_Impressão) · Vendedora 1–N Orçamento · Orçamento 1–N Arte de Orçamento · Orçamento N–1 Produto (DTF por metro).

> **Nota.** O design doc (`docs/design-doc.md`) detalha o modelo de dados para implementação (tipos, chaves, enums e o sistema de faixas de preço), que é a referência técnica que estende esta tabela conceitual.

## 9. Stack do Projeto

A escolha de tecnologias foi definida da seguinte forma (formalizada nos ADRs e detalhada no design doc):

- **Frontend:** Next.js (React) + TypeScript.
- **Backend:** FastAPI (Python). Justificativa: a RF5 (ler dimensões de imagem e desconsiderar a transparência de PNGs) e o nesting de artes do RF10 são diretos em Python, com a biblioteca Pillow e bibliotecas de empacotamento, o que torna o Python uma escolha natural para o backend.
- **Banco de dados:** PostgreSQL (relações e relatórios pedem um banco relacional).
- **Armazenamento de arquivos:** sistema de arquivos do próprio servidor de hospedagem (Hostinger). Há espaço suficiente disponível, e essa opção evita o custo e a complexidade adicionais de um storage externo.
- **Autenticação/autorização:** controle de acesso por papel (RBAC), conforme a Seção 7.
