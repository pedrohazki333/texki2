# ADR-0002 — Armazenamento de arquivos no servidor de hospedagem

**Status:** aceito · **Data:** 2026-06-18

**Contexto.** As artes (até 25 MB, PNG/PDF/TIFF) e os PNGs dos orçamentos precisam ser armazenados. O servidor de hospedagem (Hostinger) já tem espaço suficiente disponível.

**Decisão.** Armazenar os arquivos no sistema de arquivos do próprio servidor de hospedagem, e não em um storage de objetos externo.

**Consequências.**
- (+) Menor custo e complexidade no MVP.
- (−) O backup precisa cobrir explicitamente o filesystem, além do banco (ver RNF5).
- (−) Acoplamento ao servidor: uma futura migração para storage de objetos exigiria refatorar o acesso a arquivos. **Mitigação:** isolar a leitura/escrita de arquivos atrás de uma única camada de abstração, para permitir a troca futura sem espalhar mudanças pelo código.

**Alternativas consideradas.** S3 / Cloudflare R2 (descartado: custo e complexidade desnecessários para o momento).
