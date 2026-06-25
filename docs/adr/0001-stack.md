# ADR-0001 — Stack do projeto

**Status:** aceito · **Data:** 2026-06-18

**Contexto.** O TEXKI2 é a reconstrução do Texki (Laravel + Blade) com objetivo de modernizar e escalar. Duas features (RF5 — verificação de proporção lendo transparência de PNG; RF10 — nesting de artes) exigem processamento de imagem. Relatórios e as relações entre entidades pedem um banco relacional.

**Decisão.** Frontend em Next.js (React) + TypeScript; backend em FastAPI (Python); banco PostgreSQL; autorização por papéis (RBAC).

**Consequências.**
- (+) Python torna RF5 e RF10 diretos, com Pillow e bibliotecas de empacotamento.
- (+) Ecossistema maduro nas duas pontas; tipagem no frontend reduz erros.
- (−) Dois runtimes para operar e implantar (Node para o front, Python para o back).

**Alternativas consideradas.** Manter Laravel (descartado: a decisão é modernizar). Backend único em Node/TypeScript (descartado: o processamento de imagem é mais natural e robusto em Python).
