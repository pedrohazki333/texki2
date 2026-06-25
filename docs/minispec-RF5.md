# TEXKI2 — Mini-spec RF5: Verificação de proporção da arte

> Detalhamento focado da RF5. Pode viver dentro do design doc ou como anexo. A verificação é **por arte** (cada arte tem sua própria proporção).

## Objetivo
Evitar que a arte seja impressa com medidas que distorçam a imagem, garantindo que a proporção das medidas informadas seja idêntica à proporção real da arte.

## Entrada
- Uma arte em **PNG** anexada (com fundo removido).
- Medidas de impressão informadas pela vendedora: **largura** e **altura** (cm).

## Leitura da proporção
- Apenas **PNG**. O sistema lê as dimensões em pixels **desconsiderando os espaços transparentes** — ou seja, usa o *bounding box* do conteúdo não-transparente (o recorte real da arte) — e calcula `proporção = largura_px / altura_px`.
- **PDF e TIFF**: a leitura de proporção **não é ativada** (ver "Comportamento por formato").

## Regra de proporção (tolerância zero)
- A proporção das medidas informadas (`largura_cm / altura_cm`) deve ser **idêntica** à proporção lida. Tolerância: **0%**.
- Com o cadeado **fechado**, os dois campos ficam vinculados: ao editar uma medida, a outra é **recalculada automaticamente** para manter a proporção exata.
- Se forem informadas medidas que divergem da proporção (ex.: ambas digitadas ou coladas), o sistema **alerta e corrige**, ancorando na **medida digitada primeiro** e recalculando a outra.

## Cadeado (lock de proporção)
- Botão de **cadeado** para travar/destravar a correção de proporção.
- **Travado** (padrão para PNG): correção ativa, conforme a regra acima.
- **Destravado**: correção desativada; a vendedora insere qualquer largura/altura livremente, sem alerta nem recálculo.

## Comportamento por formato
| Formato | Leitura de proporção | Estado inicial do cadeado |
|---|---|---|
| PNG | Ativa (com recorte da transparência) | **Travado** |
| PDF | Inativa | **Destravado** (qualquer valor, sem correção) |
| TIFF | Inativa | **Destravado** (qualquer valor, sem correção) |

## Exemplo
Arte PNG cuja proporção lida (após recorte da transparência) é **2,00** (largura : altura).
- Vendedora digita **largura = 30 cm** primeiro → o sistema preenche **altura = 15 cm**.
- Vendedora então tenta mudar a altura para 20 cm com o cadeado fechado → o sistema corrige, mantendo a proporção a partir da medida-âncora.
- Vendedora abre o cadeado → pode digitar 30 × 20 livremente, sem correção.

## Pontos a confirmar
- **[Confirmar] Âncora quando os dois campos são editados.** Assumo o comportamento de "corrente" do Photoshop: o campo que está sendo editado vira a âncora e o outro o segue; a "medida digitada primeiro" define o primeiro recálculo. Confirmar se é isso mesmo.
- **[Confirmar] Precisão/arredondamento** da medida corrigida (ex.: 1 casa decimal / milímetro). No exemplo, uma proporção como 1,73 com largura 30 cm resultaria em altura 17,3 cm.
