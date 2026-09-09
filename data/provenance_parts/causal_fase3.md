# Fase 3 — Proveniência de §5.4 (causal), §5.5/§5.6.7 (cenários) e §5.6.4 (logit)

Autor: subagente `desenho-causal`. Data: 2026-09-08.
Documento vinculante: `docs/DESENHO_FASE3.md` (pré-registro de 2026-09-08) **mais a
EMENDA 1 (§11 do mesmo arquivo, datada 2026-09-08)**. A emenda foi escrita **depois** de
ver a série de luzes e antes de qualquer estimação; a declaração exigida pelo §10 do
pré-registro está no cabeçalho da emenda. Nenhuma afirmação de §0–§9 foi reescrita: as
afetadas estão marcadas em linha com `⟨EMENDADO 2026-09-08 · E#⟩`.

## 1. Fontes usadas nesta fase

| Série | Fonte | Nível | Selo | Papel |
|---|---|---|---|---|
| `S_HARM_soma` | **Chen, Z., Yu, B. et al. (2021)**, *ESSD* 13:889–906, DOI `10.5194/essd-13-889-2021`; dataset Harvard Dataverse `10.7910/DVN/YGIVCD` (CC0) | A | observado | quebras de 2016 e 2022 |
| `S_WSF_taxa` | DLR World Settlement Footprint Evolution, 30 m, 1985–2015 | A | observado | quebras de 2005 e 2011 |
| geometria | HDX COD-AB ADM2 (cruzamento por nome + província, nunca por P-code) | A | observado | unidades |
| população-base dos cenários | HDX COD-PS ADM2, vintage 2017 (observado) e 2025 (projeção do INE) | A | 2017 observado / 2025 **modelado** | §5.5 |
| várzea e `urbano_2025` | classificação própria (§5.1) + HAND | A | observado, **com catraca R2** | zona de proteção |

**Aviso de nomenclatura, deliberado.** Os arquivos em `data/raw/` têm prefixo
`viirs_like_li2020_v2_*`. É **herança de erro** de uma delegação anterior: o produto é o de
Chen/Yu, **não** o de Li et al. 2020 (`10.1038/s41597-020-0510-y`), que é um harmonizado
distinto. `data/raw/` não foi editado por este subagente; os `.meta.json` já trazem a
citação correta. Nenhuma saída desta fase cita Li et al. 2020.

## 2. O que a emenda mudou, em uma linha cada

- **E1** — os pré-requisitos (i) luzes e (ii) tiles WSF dos controles foram satisfeitos; **(iii) a série anual de NDVI de paisagem não foi construída**, e por isso P4 continua descritivo.
- **E2** — `S_HARM` sobe de nível B ("só validação") para **A** e vira a série primária de luz.
- **E3** — a premissa 4 (conciliar DMSP↔VIIRS por sobreposição própria) tornou-se **impossível**: VNL rebaixado a B, DMSP excluído em C. A conciliação existe, mas é interna ao produtor e **não auditável por este pipeline**.
- **E4** — **achado novo:** a costura DMSP→VIIRS é visível no dado (as seis áreas colapsam em `n>0` em 2012–2013 e todas se recuperam). Janela homogênea das luzes = **2013–2025**; pré-janela de 2016 cai de 4 para **3** pontos; 2011–2012 não servem de base pré-tratamento; **2005 e 2011 perdem qualquer corroboração de luz**.
- **E5** — a ressalva sobre 2022 **enfraquece e é reclassificada, não apagada**: a soma sobe em 2023–2025 enquanto o máximo cai, o que é dispersão da luz e não reescalonamento do produto. Continua obrigatória em toda figura da quebra de 2022, como "quebra de produto não descartada, com evidência direcional contra ela".
- **E6** — a regra de geometria por polígono ADM2 **não é executável**: os recortes espelhados são retângulos e cobrem 0,182 (Lichinga) a 1,000 (Chimoio) do ADM2 respectivo. A geometria primária passa a ser o **recorte fixo**, e ADM2 ∩ recorte vira sensibilidade, sempre com a fração de cobertura ao lado.
- **E7** — nada é afrouxado: F1–F7 como escritos, piso de p = 1/6, §8 inteiro, H4/H5/H6 rebaixadas.

## 3. Determinismo

`config/seeds.yaml`: controle sintético `13579` (20 partidas SLSQP determinísticas, a
primeira uniforme e 19 de uma Dirichlet semeada); wild cluster bootstrap `97531`, 1000
reamostragens; `logit_espacial.seed: 24680` **reservada e não usada** (§5.6.4 bloqueado).
Nenhuma etapa depende de estado de sessão; ordem no alvo `causal` do Makefile.

## 4. Aviso obrigatório sobre a inferência

Com `T ≤ 23` (WSF) e `T = 13` (luzes), o HAC **sub-cobre**: os IC publicados são **piso**
de incerteza, não teto. Com 1 tratado e 5 doadores o **p mínimo por permutação é 1/6 ≈
0,167** — nenhum resultado desta fase atinge significância convencional, e isso é aritmética
do pool, não fraqueza do efeito. Qualquer `p < 0,05` que apareça vem de inferência
assintótica sobre 6 clusters e está marcado como não confiável.

## 5. Causalidade reversa luz ↔ população

Declarada e **não resolvida**. Não há instrumento nesta AOI. O desenho proibiu resolver por
defasagem ou por VAR/Granger com esta amostra, e a proibição foi respeitada: as
elasticidades são reportadas como **associação por fase**, com a contagem de pontos na mesma
célula.

## 6. Extrapolação do GHSL

Nenhuma época GHSL 2025/2030 foi usada como âncora, série ou insumo de cenário. Os cenários
partem de COD-PS 2025 (projeção do INE, marcada `modelado`) e da classificação própria de
2025, não do GHSL.
