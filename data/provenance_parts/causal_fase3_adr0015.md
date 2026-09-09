# Fase 3 — Proveniência da execução do ADR 0015 (Emenda 2 do desenho)

Autor: subagente `desenho-causal` (§5.4, §5.5, §5.6.4, §5.6.7). Data: **2026-09-08**.
Documento vinculante: `docs/ADR/0015` e `docs/DESENHO_FASE3.md` **§12 (EMENDA 2)**.
Antecedentes: `data/provenance_parts/arbitragem_p1_2022.md` (parecer do
`revisor-adversarial`), `ORCHESTRATION_LOG.md` 3-10 e 3-11.
Complementa — não substitui — `data/provenance_parts/causal_fase3.md`.

**Natureza da emenda, declarada de saída:** é **pós-dado**. Foi motivada por contestação
do orquestrador ao veredito de P1 em 2022, arbitrada pelo `revisor-adversarial`, e a
arbitragem deu **contra quem contestou**: a queda de 2022 não está na Cidade de Tete
(2021→2022: cidade **+0,7 %**, resto do retângulo **−12,7 %**; 2021→2025: cidade
**+45,0 %**, resto **−2,5 %**). A emenda é lícita porque **não reabilita nada** — ver §4.

---

## 1. O que mudou no código

| Arquivo | Mudança |
|---|---|
| `pipeline/03_causal/placebos.py` | regra do **ramo vazio** (ADR 0015 §1) aplicada a **P1 e P2**; P1 passa a exigir IC próprio que exclua zero, como P2 sempre exigiu; colunas novas `veredito_pre_adr0015`, `mudanca_apos_adr0015`, `ramo_b2_estado`, `ramo_b3_estado`, `b2_real_ic95_inf/sup`, `b3_real_ic95_inf/sup` |
| `pipeline/03_causal/veredito_fase3.py` | propaga `veredito_pre_adr0015` e `mudanca_apos_adr0015` para `veredito_fase3.csv` |
| `pipeline/03_causal/decomposicao_luz.py` | **novo** — decomposição de §2.3, registrada como etapa não executada em ADR 0015 decisão 4 |
| `Makefile` | `decomposicao_luz.py` entra no alvo `causal`, antes de `placebos.py` |
| `docs/DESENHO_FASE3.md` | **§12, EMENDA 2** (E10, E11, E12) + três marcas `⟨EMENDADO · E10/E11⟩` em §2.3, §4.1 e §4.2 |

**Nada foi sobrescrito.** O veredito pré-ADR 0015 fica em coluna própria de
`data/processed/causal/placebos.csv` e de `veredito_fase3.csv`, ao lado do novo.

**Determinismo:** nenhum passo novo é estocástico. `config/seeds.yaml` continua sendo a
única fonte de seeds da fase e não foi alterado; `decomposicao_luz.py` não consome seed
porque não sorteia — declarado no cabeçalho do script para que a ausência não seja lida
como omissão.

---

## 2. Placebos sob a regra do ramo vazio — as quatro quebras

Artefato: `data/processed/causal/placebos.csv` (colunas `veredito_pre_adr0015`,
`veredito`, `mudanca_apos_adr0015`, linhas `unidade == AGREGADO`).

| Quebra | Série | P1 pré | **P1 novo** | P2 pré | **P2 novo** |
|---|---|---|---|---|---|
| 2005 | `S_WSF_taxa` | passa (1 replica) | **não estimável** | passa | **não estimável** |
| 2011 | `S_WSF_taxa` | FALHA (4) | **FALHA** (3) | FALHA | **passa** (afrouxamento; ver §3) |
| 2016 | `S_HARM_soma` | FALHA (5) | **FALHA** (4) | não estimável | não estimável |
| 2022 | `S_HARM_soma` | FALHA (5) | **não estimável** | passa | **não estimável** |

Motivo de cada ramo vazio, com o coeficiente de referência de Tete
(`its_quebras.csv`, variante `principal_log_HAC`):

| Quebra | `b2` de Tete (IC95) | `b3` de Tete (IC95) | ramo `b2` | ramo `b3` |
|---|---|---|---|---|
| 2005 | −0,4024 [−1,2374; +0,4327] | +0,0636 [−0,0312; +0,1584] | vazio (IC inclui 0) | vazio (IC inclui 0) |
| 2011 | +0,6129 [−0,0084; +1,2342] | −0,1830 [−0,3126; −0,0534] | vazio (IC inclui 0) | aplicável |
| 2016 | −0,1516 [−0,2148; −0,0885] | −0,1233 [−0,1449; −0,1017] | aplicável | aplicável |
| 2022 | −0,1814 [−0,2586; −0,1042] | +0,0083 [−0,0159; +0,0324] | **vazio por desenho** (ADR 0015 dec. 2/4: geometrias não comparáveis) | **vazio por E8** (inclinação pós não estimável com 4 pontos) + IC inclui 0 |

### Duas divergências em relação ao parecer do revisor

Registradas porque são informação sobre o **parecer**, não só sobre o código.

1. **2005 não "continua passa".** O parecer previa que sim. Pela regra que ele próprio
   propôs, os dois coeficientes de referência de Tete em 2005 incluem zero: **os dois
   ramos ficam vazios** e P1 em 2005 é **não estimável**. Em consequência, a condição (b)
   do parecer — "neutra em três de quatro quebras; muda só a que degenera" — **não se
   verifica**: a regra muda **duas** das quatro quebras em P1 e **três** das quatro em P2.
   A direção continua sendo de enfraquecimento, que é o que mantém a emenda lícita, mas
   a demonstração de neutralidade que o parecer ofereceu não sobrevive à execução.
2. **2016 tem 4 réplicas, não 5.** Quelimane sai: `b2` = −0,0763 com IC
   [−0,1860; +0,0333], que inclui zero, e P1 passa a exigir IC próprio que o exclua.
   Veredito inalterado: **FALHA**.

---

## 3. O único afrouxamento, e por que não é reabilitação

**P2 em 2011 vai de FALHA para "passa".** O ramo que disparava era `b2`, e o `b2` real de
Tete em 2011 (+0,613) tem IC [−0,008; +1,234] que inclui zero: não há efeito de nível a
datar. Não reabilita a quebra de 2011 porque, independentemente de P2:

- **P1 em 2011 continua FALHA** (3 controles replicam em `b3`: Chimoio, Lichinga, Xai-Xai);
- o painel `A_area_WSF|2011` continua **"CONTRAFACTUAL NÃO SUSTENTADO"** em
  `veredito_fase3.csv`, por critérios F que não dependem de placebo;
- o `b2` de 2011 é ele próprio indistinguível de zero.

A linha `mudanca_apos_adr0015` marca o afrouxamento em texto, no CSV, para que ninguém o
leia como resultado.

---

## 4. A emenda não reabilita nada — verificado por execução

`data/processed/causal/veredito_fase3.csv`, bloco `criterio_F`, após reexecução:

| painel | quebra | veredito |
|---|---|---|
| `A_area_WSF` | 2005 | CONTRAFACTUAL NÃO SUSTENTADO |
| `A_area_WSF` | 2011 | CONTRAFACTUAL NÃO SUSTENTADO |
| `B_luz_HARM` | 2016 | CONTRAFACTUAL NÃO SUSTENTADO |
| `B_luz_HARM` | 2022 | CONTRAFACTUAL NÃO SUSTENTADO |

Para 2022 especificamente, F3 e F4 continuam disparando com os mesmos números de antes da
emenda: sintético = **Inhambane com peso 1,000**; DiD **−0,12**, IC95 **[−0,28; +0,03]**,
p de permutação **0,333** (piso do pool = 1/6 = 0,167). **H4 não é reabilitada e H6
continua rebaixada.**

---

## 5. Decomposição de luz de §2.3 — executada, e o que ela permite dizer

Artefatos: `data/processed/causal/decomposicao_luz_por_camada.csv` e
`decomposicao_luz_por_camada.meta.json`. Script: `pipeline/03_causal/decomposicao_luz.py`.

**Insumos.** Luz: Chen/Yu 2021 (`10.5194/essd-13-889-2021`; Dataverse
`10.7910/DVN/YGIVCD`, CC0), 19 anos, recorte fixo `tete_aoi`, ~500 m, EPSG:4326.
Camadas: `industrial_*`, `urbano_*`, `reassentamento_*` a 30 m, EPSG:32736, seis
anos-âncora. **Reconciliação verificada:** a soma total por ano reproduz
`serie_luzes_anual.csv:soma_radiancia` com diferença máxima de **0,0004**.

**Não é uma partição, e este é o ponto principal.** Um pixel de luz cobre ~278 pixels de
camada; a repartição sub-pixel é indeterminada sem premissa sobre como a luz se distribui
dentro do pixel. Publicam-se **duas envoltórias**, nunca uma:

- **piso** — radiância repartida proporcionalmente à **área** de cada classe no pixel
  (premissa: densidade de luz uniforme; subestima classe compacta e brilhante);
- **teto** — pixel inteiro para a classe de maior prioridade presente
  (`industrial > urbano > reassentamento`), com qualquer fração > 0 (superestima).

Razão teto/piso, mediana sobre os anos: **industrial 2,12 · urbano 1,83 ·
reassentamento 5,21**. **Nenhum nível e nenhum share desta tabela é publicável como
número.** Só é afirmável o que tem **o mesmo sinal nas duas envoltórias**.

**Agregação e bordas.** Máscara 0/1 reamostrada para a grade da luz por **média**
(= fração de área da célula), `rasterio.warp.reproject`, `Resampling.average` — a única
agregação que conserva área; vizinho mais próximo perderia a classe, que é sub-pixel.
Efeito de borda: toda fronteira de classe fica difusa em ~500 m, ordem de grandeza da
própria vila de Moatize e maior que vários bairros de Tete. Após a agregação as camadas
**deixam de ser mutuamente exclusivas** no pixel de luz: 22 a 32 pixels contêm duas ou
mais classes (0 em 2000 e 2005). A prioridade do teto resolve isso por convenção, não por
medição.

**Tempo e selo.** As camadas existem só nos seis anos-âncora; a luz é anual. Máscara
categórica não se interpola: usa-se a do **ano-âncora mais próximo** (empate → âncora
anterior), com `distancia_anos_ate_ancora` em coluna. **Selo `observado` apenas quando o
ano da luz é o próprio ano-âncora; `interpolado` em todos os demais.** Toda comparação
plurianual deve ser lida na variante **`mascara_fixa_2020`**, que é invariante à mudança
de máscara e isola variação de luz de variação de classificação.

**Vieses herdados, declarados e não corrigidos** (colunas próprias no CSV):
`urbano` carrega a catraca **R2** (ADR 0013; fração do estoque herdada da união cumulativa
0 / 0 / 3,4 / 6,1 / 12,7 / **18,0 %** em 2000…2025) e a **comissão** de ADR 0009 (acurácia
do usuário de `construido` **0,286–0,625**: entre 37,5 % e 71,4 % do que a máscara chama de
construído não é construído). As duas entram **inteiras** na parcela de luz atribuída a
`urbano`. `industrial` e `reassentamento` não têm R2 (ADR 0014), mas o limiar de
`industrial` foi calibrado contra Maus em 2020 — a concordância de 2020 não é validação
independente.

### 5.1 O que a decomposição sustenta (máscara fixa de 2020; sinal igual nas duas envoltórias)

| Afirmação | piso | teto |
|---|---|---|
| 2021→2022, luz na pegada `industrial` **cai** | −15,3 % | −9,8 % |
| 2021→2022, luz em `urbano` fica **plana** (sinal ambíguo) | +2,8 % | −1,7 % |
| 2021→2025, luz em `urbano` **cresce** | +34,7 % | +32,4 % |
| 2021→2025, luz na pegada `industrial` **não recupera** | −13,9 % | −4,3 % |

### 5.2 O que ela NÃO sustenta — a restrição que importa

Contribuição de cada classe para a queda total de **−6,04 %** entre 2021 e 2022, em pontos
percentuais do total de 2021:

| classe | piso | teto |
|---|---|---|
| `industrial` | −1,94 pp | −2,54 pp |
| `urbano` | +0,77 pp | −0,89 pp |
| `reassentamento` | +0,01 pp | +0,04 pp |
| **`resto`** (sem camada classificada) | **−4,87 pp** | **−2,64 pp** |

A pegada `industrial` responde por **32 % a 42 %** da queda. O maior contribuinte isolado,
sob as duas envoltórias, está **fora** de tudo o que o pipeline classificou. Portanto, pela
decisão 4 do ADR 0015, **não é autorizada** a frase "a luz da mina caiu em 2022 e explica a
queda". O que é autorizado: *"a luz na pegada industrial caiu entre 10 % e 15 % em 2022 e
não recuperou até 2025; ela responde por cerca de um terço a dois quintos da queda do
retângulo, e o restante está em área não classificada"*.

### 5.3 Alerta de série, novo e não previsto em nenhuma emenda anterior

Entre 2013 e 2025 o crescimento do total (**+123 %**) é dominado por `resto`
(**+171 %** piso / **+427 %** teto), isto é, por pixels fora das camadas classificadas.
Compatível com (a) dispersão espacial da luz — a leitura de E5 —, (b) assentamento novo não
captado pela máscara de 2020 e (c) comportamento do produto Chen/Yu nos anos de extensão.
**As três não se separam com o conjunto A disponível.** Qualquer leitura da série de luz
como "atividade econômica da cidade" carrega esta linha junto.

---

## 6. Premissas frágeis desta execução

1. **Repartição sub-pixel indeterminada.** Teto/piso ≈ 2 em `industrial` e `urbano`, ≈ 5 em
   `reassentamento`. Nenhum nível é publicável; só sinal comum às duas envoltórias.
2. **Máscara interpolada.** Fora dos seis âncoras, a classificação é de outro ano (até 3
   anos de distância). Nenhuma quebra anual pode ser lida na decomposição.
3. **`urbano` = catraca R2 + comissão 0,286–0,625.** A parcela de luz de `urbano` cresce em
   parte por construção da regra de permanência, não por acender luz.
4. **`resto` domina.** Mais de metade da radiância, e o maior contribuinte tanto da queda
   de 2022 quanto do crescimento de 2013–2025, está fora das camadas.
5. **Geometria do recorte.** O retângulo `tete_aoi` (2.494 km²) contém a mina; os recortes
   de controle (~1.000–1.090 km²) não. A decomposição atenua, mas não elimina, o problema
   que reprovou a leitura de 2022 — porque a atenuação depende de `industrial` capturar a
   pegada, e ela cobre 76 % dos polígonos de Maus em 2025 e menos antes disso.
6. **Prioridade do teto é convenção.** `industrial > urbano > reassentamento` foi escolhida
   pela ordem de §2.3, não medida. Afeta 22–32 pixels por ano-âncora.
7. **Radiância negativa zerada** como ruído do produto, sem correção de viés — decisão de
   uma linha, declarada aqui porque não está em nenhuma emenda anterior.
8. **O afrouxamento de P2-2011** é consequência mecânica da regra, não achado. Lido
   isoladamente, faria 2011 parecer mais sólido; lido com P1-2011 (FALHA) e com o critério
   F (não sustentado), não faz.
