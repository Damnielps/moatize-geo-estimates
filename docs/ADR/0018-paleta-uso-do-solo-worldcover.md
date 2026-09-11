# ADR 0018 — Cores das classes de uso do solo pela legenda ESA WorldCover (FAO LCCS)

- **Data:** 2026-09-11
- **Fase:** 4b (painel)
- **Decidido por:** usuário ("utilize as cores padrão internacionais para classificação do uso do solo"); padrão e adaptações escolhidos pelo orquestrador
- **Estado:** aceito

## Contexto

As classes do mapa usavam a identidade Ardósia (ardósia, terracota, verdes discretos). Isso
tem dois custos para um leitor técnico: as cores não correspondem a nenhuma convenção de
cobertura do solo, e a pegada minerária aparecia em terracota, tom próximo do vermelho que as
legendas internacionais reservam para área construída.

## Decisão

Adotar a legenda oficial da **ESA WorldCover**, que implementa o sistema da FAO **LCCS**
(ISO 19144-2) e já é fonte de nível A do estudo. Os hex foram lidos da tabela de cores embutida
no raster original da ESA, não de memória. Fonte única: `config/paleta_uso_solo.yaml`, lida pelo
app e pelas figuras.

| Classe do estudo | Classe WorldCover | Cor | Origem |
|---|---|---|---|
| urbano (orgânico) | 50 Built-up | `#FA0000` | oficial |
| reassentamento | 50 Built-up | `#9E0000` + contorno | adaptação |
| industrial/minerária | 60 Bare / sparse vegetation | `#B4B4B4` + contorno | adaptação |
| cultivo irrigado / vazante | 40 Cropland | `#F096FF` | oficial |
| cultivo de sequeiro (candidata) | 40 Cropland | só contorno tracejado | adaptação |
| água | 80 Permanent water bodies | `#0064C8` | oficial |
| várzea (zona) | 90 Herbaceous wetland | `#0096A0`, opacidade 0,25 | adaptação |
| adensamento 2020→2025 (modelado) | 50 Built-up | hachura/contorno, sem preenchimento | adaptação |

## Alternativas rejeitadas

- **Anderson/USGS (NLCD)**: convenção norte-americana, com classes de desenvolvimento por
  intensidade que o estudo não mede.
- **Dynamic World**: paleta de um produto, não de um sistema de classificação; é fonte de nível B
  neste estudo (acesso só via GEE).
- **MapBiomas**: legenda nacional brasileira, sem correspondência com a África Austral.
- **Manter a Ardósia nas classes**: descartado pelo pedido do usuário. A Ardósia continua na
  interface (tipografia, cabeçalho, gráficos que não são classes de uso do solo).

## Adaptações e o que elas custam

WorldCover não tem mineração nem reassentamento. A mina vai para Bare/sparse porque cava e pilha
de estéril são solo exposto em LCCS, e porque nunca pode ter a cor de área urbana (§10). O
reassentamento é área construída em LCCS; recebe um tom escuro do Built-up com contorno, porque
a separação entre crescimento orgânico e reassentamento é obrigatória (§0). A distinção entre os
dois vermelhos é menor que a anterior; o contorno e a legenda compensam. A várzea é zona modelada,
não cobertura; usa a cor de Herbaceous wetland em baixa opacidade. Toda adaptação é marcada
`origem: adaptacao` no YAML e aparece como tal na legenda do app.
