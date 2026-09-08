# ADR 0004 — Divergência entre catálogos STAC (Planetary Computer × Element84) e escolha do catálogo canônico

- **Data:** 2026-09-07
- **Fase:** 1 (Pipeline de imagem — compostos e índices)
- **Decidido por:** `pipeline-imagem`
- **Estado:** aceito

## Contexto

`data/provenance_parts/imagem.md` (Fase 0') registrou, sem resolver, uma divergência
de contagem entre os dois candidatos a catálogo STAC de referência (§11.3 rota b):

| ano/coleção | Planetary Computer (PC) | Element84 Earth Search (E84) |
|---|---|---|
| `sentinel-2-l2a` 2020 (mai–out, nuvem ≤40%) | 103 | 194 |
| `landsat-c2-l2` 2025 (mai–out, nuvem ≤40%) | 16 | 18 |

Esta tarefa (Fase 1) precisava escolher **um** catálogo canônico para
`pipeline/01_imagery/compostos.py` e investigou as duas causas.

## Investigação

### 1. Acesso sem conta (§11.3 exige que a rota (b) "não exija conta")

Testado por leitura real de pixel (não só busca de metadados):

- **E84 → `landsat-c2-l2`**: os assets resolvem para
  `s3://usgs-landsat/collection02/...`. Leitura anônima
  (`AWS_NO_SIGN_REQUEST=YES`) falha com
  `AccessDenied: Anonymous users cannot invoke requests against Requester Pays
  buckets. Please authenticate.` — este bucket da AWS Open Data é
  **Requester Pays**: exige uma conta AWS com faturamento ativo para qualquer
  leitura, mesmo de uma única janela recortada por COG. Isso viola
  diretamente a exigência de §11.3(b).
- **PC → `landsat-c2-l2`**: os mesmos dados (mesma origem USGS C2 L2), servidos
  via Azure Blob Storage com URL assinada (SAS) obtida anonimamente por
  `planetary_computer.sign_inplace`. Leitura de pixel bem-sucedida sem
  qualquer credencial, chave ou conta.
- **E84 → `sentinel-2-l2a`**: os assets resolvem para
  `s3://sentinel-cogs` (bucket público, **não** Requester Pays). Leitura
  anônima funciona.
- **PC → `sentinel-2-l2a`**: também funciona anonimamente (SAS).

**Conclusão parcial:** para Landsat, só o Planetary Computer atende à exigência
"não exige conta". Element84 é inutilizável para Landsat nesta tarefa sem
contratar acesso AWS — não é uma alternativa livre, apesar do catálogo em si
ser público.

### 2. Causa da divergência de contagem — `landsat-c2-l2` 2025 (16 × 18)

Comparação item a item (mesma AOI, mesma janela mai–out/2025, nuvem ≤40%):

```
only E84: LC09_L2SP_168071_20250703_02_T1, LC09_L2SP_168071_20250921_02_T1,
          LC09_L2SP_168071_20251023_02_T1
only PC:  LC09_L2SP_168071_20250516_02_T1
```

Buscando **sem** filtro de nuvem no PC para o ano inteiro de 2025, as três
datas `2025-07-03`, `2025-09-21` e `2025-10-23` **não existem em nenhuma
consulta ao PC** — não é uma diferença de filtro de nuvem nem de política de
reprocessamento, é uma **lacuna de indexação real**: o PC simplesmente não
ingeriu essas três cenas Landsat 9 do path/row 168/071 (confirmado também
comparando a série completa de 2000/2005/2010/2015/2020, onde PC e E84 batem
exatamente — a lacuna é específica de 2025, o ano mais recente). Hipótese mais
provável: atraso de sincronização do pipeline de ingestão do PC em relação ao
USGS/AWS, sem indicação de quando (ou se) será corrigida.

### 3. Causa da divergência de contagem — `sentinel-2-l2a` 2020 (103 × 194)

Comparação de IDs mostrou que o E84 mantém **múltiplos itens para a mesma
aquisição física**, com sufixo `_0`/`_1`/`_2` no id. Exemplo confirmado:

```
S2A_36KWG_20200503_0_L2A  — datatake GS2A_20200503T073621_025400, baseline N02.14
S2A_36KWG_20200503_1_L2A  — datatake GS2A_20200503T073621_025400, baseline N05.00
```

Mesmo `datatake_id`, mesmo `bbox`; a única diferença é a **versão de
reprocessamento** (baseline `N02.14` vs. `N05.00`, alterada por reprocessamento
posterior da ESA). O E84 indexa a aquisição original **e** cada reprocessamento
subsequente como itens STAC separados; o PC indexa só uma versão (aparentemente
a mais recente) por aquisição/tile. A proporção observada (194/103 ≈ 1,88)
é consistente com "quase o dobro de itens porque quase toda aquisição tem uma
versão duplicada".

**Isto não é uma diferença de cobertura real — é duplicação de contagem.** Se
`compostos.py` usasse o E84 sem filtrar por baseline, o composto de mediana
contaria a mesma cena Sentinel-2 quase duas vezes, distorcendo a mediana em
favor de imagens reprocessadas mais vezes (viés não aleatório: cenas mais
antigas dentro da janela tiveram mais tempo para acumular reprocessamentos).

## Decisão

**Planetary Computer (`https://planetarycomputer.microsoft.com/api/stac/v1`,
com `planetary_computer.sign_inplace`) é o catálogo STAC canônico** de
`pipeline/01_imagery/compostos.py`, para Landsat e para Sentinel-2, por dois
motivos que se reforçam:

1. É o único dos dois que atende "não exige conta" para Landsat (E84 exige
   uma conta AWS com faturamento para o bucket Requester Pays do USGS).
2. Para Sentinel-2, o PC já entrega um item por aquisição física, evitando o
   trabalho (e o risco de erro) de deduplicar baselines de reprocessamento
   manualmente — o que seria necessário se o E84 fosse usado.

**Custo aceito:** uma lacuna de cobertura conhecida e pequena em 2025
(3 cenas Landsat 9 ausentes do PC, de um total de 19 no E84 — sobra ainda
16 cenas, acima do piso de 5–8 cenas citado em `data/provenance_parts/imagem.md`
para um composto de mediana robusto, e complementado por 162 cenas Sentinel-2
em 2020/2025). Registrado explicitamente aqui e no `.meta.json` de cada
composto de 2025, não escondido.

## Alternativas rejeitadas

- **Element84 para tudo.** Rejeitada: inviabiliza Landsat sem conta AWS,
  quebrando o requisito central de §11.3(b).
- **Híbrido (PC para Landsat, E84 para Sentinel-2).** Considerada e
  rejeitada por complexidade desnecessária: o PC já resolve os dois sem
  conta e sem duplicação, então misturar catálogos só aumentaria a superfície
  de manutenção (duas políticas de assinatura de URL, dois esquemas de nome
  de asset) sem ganho de cobertura que justifique.
- **Deduplicar E84 por baseline e usar E84 para tudo.** Rejeitada por ora:
  resolveria a duplicação do Sentinel-2, mas não resolve a exigência de conta
  AWS para Landsat, que é a restrição mais dura.

## Consequência

- `pipeline/01_imagery/_stac_common.STAC_ENDPOINT_CANONICO` aponta para o PC.
- `pipeline/01_imagery/compostos.py` grava, no `.meta.json` de cada composto,
  o catálogo usado e a lista de ids de cena — qualquer auditoria futura pode
  conferir contra o E84 e encontrar exatamente esta divergência documentada.
- Se o PC preencher a lacuna de 2025 num reingesto futuro, a reexecução do
  script vai automaticamente capturar as cenas adicionais (nenhuma lista de
  cena é fixada em código) — não é necessário revisitar este ADR, só
  reexecutar e observar a contagem mudar no novo `.meta.json`.
- Revisar este ADR se o PC vier a apresentar lacunas de indexação em anos
  âncora além de 2025, ou se o E84 mudar a política do bucket Requester Pays.
