# REPROVADO — `FASE0_DEMOGRAFICAS_SUMMARY.md`

Reprovado pelo `qa-validador` no portão da Fase 0' (2026-09-07), motivo 1.

Resumo executivo deixado pela **primeira** execução da família demográfica, em T1 — a mesma
que foi reprovada por verificar âncoras contra agregador (ver `ORCHESTRATION_LOG.md` 0'-02).
Ficou solto em `data/`, sem referência de nenhum outro artefato e sem marca de que fora
superado, convivendo com `DATA_AUDIT.md` e `LICENSES.md` como se ainda valesse.

O que ele afirma, e por que não pode ficar:

- verifica as seis âncoras de §8 contra `citypopulation.de` e Wikipedia, marcando-as "✓ OK";
- recomenda textualmente **"Usar para publicação"** o valor de 307.338 com base nessas
  fontes secundárias.

Contraria §4.0 regra 4 (agregador serve para localizar, nunca para citar) e o veredito de
`data/DATA_AUDIT.md`, que classifica os documentos do INE como nível C e conclui que
**nenhum número populacional sustenta conclusão do núcleo**.

O conteúdo está superado por `data/{licenses,provenance}_parts/demograficas.md`, onde as
âncoras de 2007 e 2017 foram confirmadas contra documento primário do INE recuperado do
Internet Archive, e a de 1997 está registrada como NÃO LOCALIZADA.

Coincidência a registrar: o valor 307.338 é o mesmo do Quadro 3 do IV RGPH. Chegar ao
número certo pelo caminho errado não valida o caminho — e o mesmo arquivo dá 305.722 como
alternativa plausível, valor que **não consta de nenhum documento primário**.
