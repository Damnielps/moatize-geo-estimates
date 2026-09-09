# DATA_AUDIT.md — Fase 0', Portão de Auditoria (§4.0, regra 5)

Consolidado em 2026-09-07 a partir de `data/LICENSES.md`, `PROVENANCE.md` e dos
fragmentos por família em `data/licenses_parts/` e `data/provenance_parts/`.
Este documento resolve toda linha `pendente_auditoria` e emite o veredito de
abertura da Fase 1.

---

## 0. RECONCILIAÇÃO OBRIGATÓRIA — Revisão de 2026-09-08 (pós-medição, ADR 0012/0013/0014)

A revisão de 2026-09-07 (seção 0, abaixo) julgava **disponibilidade de dado**: a fonte
existe, tem licença A, cobre o período. Três ADRs posteriores — `docs/ADR/0012`
(2026-09-08), `docs/ADR/0013` (2026-09-08) e `docs/ADR/0014` (2026-09-08) — mediram
**desempenho da classificação**, não disponibilidade, e a medição derruba parte do
veredito anterior. O dado orbital existe; o classificador de cultivo não separa cultivo
de vegetação natural, e a série de área construída própria (e o WSF Evolution) é
catraca por construção. Isto muda o veredito de H5, H6, P8, e qualifica P1–P4, H1–H4,
P6 e P7. A seção 1–4 abaixo é preservada sem alteração de texto; esta seção a supera
onde indicado.

### H5 rebaixada: de "RESPONDÍVEL, com ressalva de fenologia" para SUSTENTADA FRACAMENTE

`docs/ADR/0012` mediu `cultivo_sequeiro` com acurácia do usuário **0,000** (n=8,
IC95 ±0,000) e kappa **−0,065** — pior que aleatório. `docs/ADR/0014` corrigiu a raiz
(limiar relativo, propagado de `docs/ADR/0011`) e o cultivo **não melhorou**: o
Jaccard contra GLAD Cropland/ESA WorldCover permanece em **0,001–0,002**, e a área
classificada (359–761 km²) excede a do GLAD (~20 km² na mesma AOI) por mais de uma
ordem de grandeza. Isso localiza a falha na abordagem fenológica bianual, não nos
limiares — **reforça**, não enfraquece, `docs/ADR/0012`.

H5 tem dois componentes: (i) "conversão cropland→construído concentrada na
implantação/boom" — **não sustentável**: não existe classificação de cropland
defensável em nenhum ano-âncora para medir a conversão, com nenhuma das duas classes
(`cultivo_sequeiro` reprovado; `cultivo_irrigado` cobre só cultivo irrigado, uma fração
pequena e distinta do que a hipótese descreve); (ii) "persistência em várzeas" —
**sustentável apenas de forma fraca e indireta**: `cultivo_irrigado` (acurácia do
usuário 0,556 ± 0,344, Jaccard 0,043–0,098 contra GLAD/WorldCover — positivo e acima do
acaso, mas com intervalo de confiança que cobre quase toda a faixa plausível) aparece
2 a 3 vezes mais concentrado na zona de várzea do que `cultivo_sequeiro` em 4 dos 6
anos-âncora. Essa razão **não é uma medida de área agrícola** — é enriquecimento
relativo entre duas classes, uma das quais (o denominador da comparação,
`cultivo_sequeiro`) tem acurácia nula. **Veredito revisto: H5 sustentada fracamente**,
apenas no componente de localização relativa em várzea, nunca em magnitude de área ou
de conversão.

### H6 rebaixada: de "PARCIAL" para SEM RESPOSTA — e o motivo muda

O veredito de 2026-09-07 tratava H6 como parcial por falta de dado domiciliar (censo/IOF
em nível C, sem reprocessador). Essa lacuna **continua existindo**, mas deixou de ser o
fator limitante. O fator limitante agora é que **a série de área de cultivo que
sustentaria "cresce a área cultivada intra e periurbana após 2016" não mede cropland**:
kappa −0,065, Jaccard essencialmente nulo contra duas referências externas
independentes, em todos os pares ano testados. Não há segunda via de nível A com
desempenho medido para a dimensão de área. **Veredito revisto: SEM RESPOSTA** — nem a
dimensão física (área cultivada) nem a dimensão domiciliar (dependência de produção
própria) têm via de nível A com desempenho aceitável.

### Pergunta 8 de §1 — respondível só em localização de várzea e cultivo irrigado com ressalva

"Onde estão os bolsões" é respondível em parte: várzea (HydroRIVERS + DEM, nível A,
método geométrico não sujeito ao mesmo defeito) e `cultivo_irrigado` com a ressalva de
acurácia acima. "Quanto ocupam" e "como evoluíram" (conversão em construído,
deslocamento para anéis externos, persistência) **não são respondíveis** com a série
atual — dependem de uma medida de área de cultivo que não existe em nível A com
desempenho defensável. O papel na segurança alimentar e renda domiciliar permanece
fechado por ausência de tabulação em A (Censo/IOF = C), como já registrado.

### P1/H1 — reformulação adicional: taxa de primeira detecção, não estoque

Emenda de 2026-09-08 a `docs/ADR/0008`, corroborada por `docs/ADR/0013`: o WSF
Evolution, posto como série primária de tendência pelo ADR 0008 original, é também
**monotônico por construção** — cada pixel registra o ano de primeira detecção, e o
acumulado nunca decresce. **Nenhuma fonte disponível fornece estoque de área construída
sem monotonicidade imposta** (nem a classificação própria, com a regra R2 de
permanência mantida em `urbano`; nem o WSF, pelo formato do próprio dado). H1
(reformulada por `docs/ADR/0003` em área construída) permanece testável em nível A,
mas com uma segunda reformulação obrigatória: a hipótese é sobre a **taxa de
incorporação de solo** (primeira detecção por ano), não sobre o nível do estoque. As
quebras de 2005 e 2011 são estimáveis sobre essa taxa; nenhuma quebra é estimável sobre
o acumulado. Veredito: **TESTÁVEL EM A, restrito a taxa de primeira detecção** — grau
abaixo do "TESTÁVEL EM A" simples da revisão de 2026-09-07.

### P2 e P6 — o par 2015–2020 da série própria está contaminado

`docs/ADR/0013` mostra que a área bruta de 2015 está inflada (~15 km²) por colapso do
pool de treino de `solo_exposto` naquele ano (18× menos amostras que em 2000/2025), e
que o GHSL (árbitro externo, épocas observadas) não mostra queda alguma entre 2015 e
2020 — quem precisa de explicação é o excesso de 2015, não o déficit de 2020. **A
quebra de 2016 cai exatamente entre os dois anos-âncora contaminados.** Isso atinge
diretamente P2 (fim do boom) e P6 (bust 2015–2019): nenhum efeito de nível estimado
sobre o par 2015–2020 da série própria pode ser atribuído ao ciclo do carvão — mede o
artefato de rotulagem, não o tratamento. `docs/ADR/0013` recomenda que a série de luzes
noturnas (harmonizada DMSP-VIIRS / VIIRS DNB, que não é catraca e pode cair) passe a ser
a série primária de §5.4 depois de 2015. P2 permanece PARCIAL; P6 permanece PARCIAL, com
a ressalva adicional de que a magnitude do bust não pode vir da série própria de área
construída no par 2015–2020.

> **Nota da revisão de 2026-09-08, tarde (ver §0'', auditoria de Fase 3):** a
> recomendação acima de usar "a série de luzes noturnas... que não é catraca e pode
> cair" como série primária pós-2015 **foi parcialmente esvaziada**: o único
> harmonizado de nível A hoje em `data/raw/` é o produto Chen/Yu (NPP-VIIRS-like,
> Harvard Dataverse), cuja conciliação interna DMSP↔VIIRS não é auditável por este
> pipeline, e que apresenta uma descontinuidade não resolvida entre 2020 e 2022. Ver
> §0''.

### P3 — melhora parcialmente: abandono volta a ser observável

`docs/ADR/0014` removeu a regra R2 de `reassentamento` (e de `industrial`), por decisão
do usuário sobre o diagnóstico do ADR 0013 item 5. A série deixou de ser monotônica:
1,20 (2010) · 1,65 (2015) · 0,70 (2020) · 1,09 (2025) km². Isso é uma melhora direta
para a pergunta 3 de §1 ("como evoluíram — consolidação, **abandono**, adensamento"):
o abandono, antes indetectável por construção, agora é observável na série própria.
Isso **não resolve** as duas lacunas já registradas na arbitragem (b) — ausência de
polígono oficial do plano de reassentamento (logo, "quanto ocupam" continua sem fonte
A) e ausência de contagem de famílias em A (HRW é B). Veredito atualizado: **PARCIAL,
com o componente "evolução temporal" agora sustentado por observação própria não
catraca** (com o aviso de que a série vem de um buffer fotointerpretado ao redor do nó
OSM, não de um polígono do plano — a atribuição causal "isto é o reassentamento"
permanece frágil).

### P4 e H2 — típologia por pixel precisa da ressalva de churn

`docs/ADR/0013` mede, para `urbano`, um churn pixel a pixel de **31–54 %** entre
anos-âncora consecutivos (Jaccard 0,456–0,69): a estabilidade em área agregada não se
traduz em estabilidade de localização. Isso atinge diretamente qualquer método que
dependa do mesmo pixel manter identidade entre dois anos — matriz de transição, rosa de
expansão, tipologia infill/borda/leapfrog (§5.2, §5.6.4), que é exatamente o método por
trás de P4 e H2. **Veredito revisto: RESPONDÍVEL COM RESSALVA DE CHURN** (antes:
RESPONDÍVEL sem qualificação) — a área agregada por tipologia é utilizável, a atribuição
pixel a pixel de qual tipologia gerou qual incremento carrega 31–54 % de incerteza de
identidade e deve declarar esse número em toda figura e tabela.

### H3 — componente industrial melhora, componente demográfico inalterado

A remoção de R2 de `industrial` (`docs/ADR/0014`, item 3) é uma melhora para H3: antes,
a permanência mascarava reabilitação de cava/pilha de estéril (`docs/ADR/0011` item 5–6
já registrava isso); agora a série pode cair, o que é necessário para testar
"estabiliza após 2016" de forma não circular. O componente "mancha urbana cresce por
inércia demográfica" permanece como estava em 2026-09-07 (dependente de HDX 2017
observado + 2025 modelado, insuficiente sozinho) — **inalterado nesse componente**, e
adicionalmente sujeito à ressalva de churn de P4/H2 se usar tipologia por pixel.

### H4 — a série própria de `urbano` não pode testar a hipótese; usar GHSL observado ou série de luzes

`docs/ADR/0013` (seção "Não pode") é explícito: a regra R2 em `urbano` faz o incremento
publicado ser sempre ≥ 0 por construção, então uma elasticidade área–luz estimada com
essa série produziria "área cresce, atividade estagna" **mesmo se H4 fosse falsa** —
circularidade, não resultado. A evidência principal de H4 já estava condicionada, na
revisão de 2026-09-07, a não depender da população modelada de 2025 (risco de
circularidade análogo do lado demográfico); agora se soma a restrição do lado da área:
usar GHSL BUILT-S em épocas **observadas** (não R2025 extrapolado) ou a coluna
experimental `estoque_sustentado_pelo_ano_km2` (que pode cair, e cai em 2020), nunca a
série R2 publicada de `urbano`. Veredito revisto: **PARCIAL, com risco de circularidade
duplo (lado população E lado área) — não sustenta conclusão sozinha em nenhuma das duas
pontas**, condição mais restrita que a de 2026-09-07.

### O que não muda nesta revisão

Arbitragens (a) INE-documento=C, (c) WorldPop=A da seção 1; a tabela de níveis A/B/C da
seção 2; P5 (luzes vs. ciclos do carvão, método não afetado pelos três ADRs); o bloqueio
de 1997/2007 fora do núcleo A; e as condições de abertura por módulo da seção 4,
**exceto** onde a presente seção as qualifica. O veredito global permanece **CONJUNTO A
INSUFICIENTE**, agora por dois motivos independentes e não apenas um: (i) lacunas de
licença/proveniência (1997/2007, tabulações domiciliares do INE — inalterado desde
2026-09-07) e (ii) lacunas de desempenho de classificação recém-medidas (cultivo,
monotonicidade de área construída) que impedem H5/H6/P8 de se apoiarem em número, e que
qualificam H1/H3/H4/P2/P4/P6/H2 mesmo onde a fonte é A.

---

## 0''. Auditoria da coleta de Fase 3 (2026-09-08, tarde) — luzes noturnas, WSF de controle, HDX COD-AB

Classifica três famílias coletadas em `data/licenses_parts/fase3_coleta_t2_licenca.md`
(registradas pelo coletor como "não classificado — cabe ao auditor-dados") e duas
fontes não obtidas. Detalhe linha a linha em `data/licenses_parts/fase3_auditoria_t3.md`
e `data/provenance_parts/fase3_auditoria_t3.md`. Resumo:

| # | Fonte | Nível | Nota |
|---|---|---|---|
| 1 | NPP-VIIRS-like (Chen, Z., Yu, B. et al.), 54 recortes, Harvard Dataverse V10, DOI 10.7910/DVN/YGIVCD | **A** | CC0 1.0, confirmada na API do Dataverse (não agregador). **Atribuição corrigida**: não é "Li et al. 2020" (produto distinto, figshare, DOI 10.1038/s41597-020-0510-y) — ver correção abaixo. |
| 2 | WSF Evolution — 5 tiles das capitais de controle (DLR) | **A** | CC BY 4.0, mesma licença já registrada para os tiles da AOI de estudo em `construida.md`. |
| 3 | HDX COD-AB Moçambique (`moz_admin_boundaries.geojson.zip`) | **A** | CC BY-IGO 3.0, mesma lógica já aplicada ao HDX COD-PS (reprocessador com licença própria, distinto do documento-INE bruto). |
| 4 | VIIRS VNL V2 (EOG, `eogdata.mines.edu`) | **B — rebaixada de A** | Todo diretório de download testado responde HTTP 302 → OAuth (`eogauth.mines.edu`); não é acesso anônimo nem cadastro trivial. O registro pré-existente em `economicos.md` ("acesso via GEE ou EOG FTP público", nível A) está **desatualizado**: o FTP público não existe mais. Rota via GEE não testada nesta rodada. |
| 5 | DMSP-OLS estável (NOAA/NCEI) | **C — excluída** | URL de `CLAUDE.md` §4.4 responde HTTP 404; página sucessora em EOG sofre o mesmo bloqueio OAuth do item 4; nenhuma licença localizável no domínio que efetivamente serve o dado hoje. |

### Correção obrigatória a `CLAUDE.md` §4.4

A linha "Harmonized DMSP-VIIRS Nighttime Lights (1992–2018) (Li et al. 2020)" do
mandato descreve um produto diferente do que está em `data/raw/`. O que foi coletado é
"The global NPP-VIIRS-like nighttime light data (Version 2) for 1992–2025", autoria
**Chen, Z., Yu, B., Yang, C., Zhou, Y., Yao, S., Qian, X., Wang, C., Wu, B., Wu, J.**
(paper de método: *Earth Syst. Sci. Data*, 13, 889–906, 2021, DOI
10.5194/essd-13-889-2021), hospedado no Harvard Dataverse (DOI 10.7910/DVN/YGIVCD,
CC0 1.0) — **não** em figshare, e **não** do grupo Li/Zhou/Zhao/Zhao (Scientific Data
7, 168, 2020). As duas séries são harmonizados DMSP↔VIIRS **distintos**, de grupos e
métodos diferentes. `CLAUDE.md` §4.4 deve separar as duas linhas; o produto Li et al.
2020 não foi coletado nesta Fase e permanece nível B conforme já registrado (acesso via
figshare exige verificação adicional não feita aqui).

### Resposta à pergunta pré-registrada: a conciliação DMSP↔VIIRS interna ao produtor é aceitável sob §4.0?

**Não, não sem ressalva formal — e a ressalva deve constar de toda figura/tabela que
use a série pós-2015.** Com VIIRS VNL rebaixado a B e DMSP-OLS excluído (C), o único
harmonizado de nível A é o produto Chen/Yu, que resolve a calibração cruzada
DMSP↔VIIRS **dentro de seu próprio modelo de super-resolução/aprendizado profundo**,
sem parâmetros auditáveis por este pipeline. Isso substitui a premissa 4 de
`docs/DESENHO_FASE3.md` §1.3 — conciliação **estimada por nós**, com trecho de
sobreposição 2012–2013, critério de falha e placebo próprios (P4, §4.4 do desenho) —
por uma conciliação de caixa-preta de terceiros. Sob §4.0, o dado em si é A (CC0,
proveniência primária confirmada); o que deixa de ser possível é a **verificação
independente** da conciliação, que o desenho pré-registrado presumia disponível via
duas séries A separadas.

Isso é agravado pela descontinuidade medida pelo orquestrador: radiância máxima na AOI
de Tete cai de 70,4 (2020) para 49,9 (2022) e permanece em 49,9 até 2025. Evidência de
terceiros (não o changelog interno do Dataverse, que este agente não conseguiu renderizar)
indica que o produtor **reprocessou especificamente os anos 2021–2022** desta linhagem
de dataset. A coincidência temporal entre a queda medida e um reprocessamento
documentado do produto **não permite, com os dados hoje em `data/raw/`, distinguir
quebra de produto de quebra de economia na quebra causal de 2022** prevista em
`docs/DESENHO_FASE3.md` §1.2. Nenhuma fonte B (o próprio harmonizado seria nível B se
não fosse pela via CC0 do Dataverse — aqui a licença salva o nível, não a auditabilidade)
resolve isso.

**Veredito**: aceitável **apenas** como a única via disponível de série de luz de nível
A, nunca como equivalente metodológico ao desenho original de conciliação por
sobreposição. Toda quebra estimada sobre esta série a partir de 2020–2022 deve carregar
o aviso explícito: "não distinguível de mudança de versão do produtor entre 2020 e
2022 — nenhuma fonte de nível A permite verificação independente." Recomenda-se emenda
datada a `docs/DESENHO_FASE3.md` (seu próprio §10 de pré-registro) registrando esta
mudança de disponibilidade de dado.

### Efeito sobre a matriz da seção 3 e sobre o veredito global

Nenhuma pergunta/hipótese muda de categoria (RESPONDÍVEL/PARCIAL/SEM RESPOSTA) só por
esta auditoria: P5, P6 e H4 já estavam condicionados (ver §0' acima) a usar luzes como
série primária pós-2015, e essa recomendação **permanece a melhor disponível** — só
deixa de ser "verificável de forma independente", o que já era um risco declarado
(circularidade, §0' H4) e agora ganha um segundo risco declarado (versão do produto).
O veredito global **não muda**: continua **CONJUNTO A INSUFICIENTE**, pelos dois
motivos já registrados em §0, mais este terceiro risco explícito sobre a série de luz
pós-2020, que não rebaixa nenhuma pergunta a um grau pior do que já estava, mas deve
constar de toda publicação que use a quebra de 2022.

---

## 0. Revisão de 2026-09-07 (pós-emissão) — o que muda e o que não muda

Quatro fatos novos, verificados após a emissão original deste documento (seção 1
em diante, preservada abaixo sem alteração de texto, apenas anotada onde a revisão
a supera). Resumo do julgamento:

1. **HDX COD-PS (CC BY-IGO 3.0) já estava listado como nível A** na tabela da
   seção 2 deste documento ("Demográfica | HDX COD-PS... cobre só 2017+"), mas a
   matriz da seção 3 e o veredito da seção 4 não tinham extraído toda a
   consequência disso: tratavam 1997/2007/2017 como um bloco único "removido"
   pela reclassificação C dos documentos do INE. Isso estava **parcialmente
   incorreto**. Distinção necessária, aplicada agora: a classificação C atinge o
   **documento do INE como objeto** (o PDF/XLS/HTML do censo); não atinge um
   **valor numérico idêntico, obtido de um reprocessador com licença própria**
   verificável (HDX/OCHA, sob CC BY-IGO, que é variante nomeada de CC-BY em
   §4.0). Cidade de Tete 307.338 e Moatize 260.843 (2017) **têm caminho de nível
   A independente do INE** e passam a poder sustentar número publicado — com
   citação ao reprocessador (HDX/OCHA/FIS, fonte declarada INE) e a ressalva já
   registrada em `data/LICENSES.md`/`PROVENANCE.md` de que os limites ADM3/ADM4
   subjacentes carregam "ajustes não oficiais" até a revisão INE de 2027, e de
   que o valor é contagem residente **sem** o ajuste de omissão — 3,8% na Província de Tete (a taxa pertinente às unidades deste estudo) e 3,7% no total nacional; são duas taxas de unidades diferentes, não uma faixa de incerteza de uma só grandeza
   documentado na brochura nacional (ver `demograficas.md`, achado (b)).
2. **Existe agora uma segunda âncora HDX, vintage 2025** (Cidade de Tete
   460.248; Moatize 349.103), mesma licença A, mesmo reprocessador — mas com
   selo **`modelado`** (`.meta.json` já grava isso): é projeção do INE, não
   recontagem. Isso dá à pergunta 6 de §1 um segundo ponto quantitativo em nível
   A, 8 anos depois do único ponto observado (2017). **Não resolve** a pergunta
   6 por completo: dois pontos (um observado, um modelado) não caracterizam
   "desaceleração, estagnação ou reconversão" com a mesma força que uma série;
   e há um risco de **circularidade metodológica** a registrar explicitamente
   — se a projeção do INE para 2025 assume uma taxa de crescimento geométrica
   fixa (método padrão de projeções demográficas oficiais), ela não pode, por
   construção, revelar uma desaceleração real induzida pelo bust do carvão: o
   dado projetado incorporaria a hipótese que se quer testar. Isso é
   particularmente crítico para **H4** (luzes descolam da população pós-2016):
   usar uma população 2025 modelada por extrapolação geométrica para testar se
   a população "continuou crescendo enquanto a economia estagnou" arrisca
   confirmar H4 por construção do próprio dado, não pela evidência. **Uso
   permitido apenas com esse aviso method­ológico explícito e visível** (no
   tooltip de proveniência do app e na metodologia do artigo), nunca como prova
   independente de desacoplamento.
3. **1997 permanece fora do núcleo A.** A via UNSD Demographic Yearbook 2007
   (Tabela 8) **confirma** 101.984 para a Cidade de Tete, mas sob licença da
   ONU que proíbe redistribuição e obra derivada — **nível B**, exatamente como
   o IPUMS. Classificação mantida/confirmada: **B**, não A. Serve para
   validação cruzada rotulada, nunca para número publicado no núcleo. Moatize
   distrito 1997 e ambos os valores de 2007 (Tete e Moatize) **continuam sem
   nenhuma via A ou B** identificada nesta rodada. CIESIN/SEDAC — a via mais
   promissora, porque o GPW publica os insumos administrativos originais do
   III/IV RGPH — está **fora do ar (timeout, não 404)**: registrado como "via
   não esgotada por indisponibilidade externa", categoria distinta de "dado
   inexistente". Reexecutar quando o domínio voltar.
4. **H1 é reformulada por ADR 0003** (`docs/ADR/0003-linha-de-base-por-area-
   construida.md`, aceito): a linha de base 1997–2005 passa a ser testada por
   **área construída** (WSF Evolution, DLR, CC-BY-4.0, nível A, 30 m, anual
   1985–2015), não por população recenseada. Isso torna **H1 plenamente
   testável em nível A** — na verdade com resolução temporal superior à
   formulação original: 19 observações anuais no pré-tratamento (1985–2015)
   contra 3 pontos censitários, o que **fortalece**, não enfraquece, o teste de
   tendência paralela de §5.4. O ganho é estrutural, não cosmético: a pergunta
   de pesquisa muda de "a população acelerou de X%/ano para Y%/ano" para "a
   mancha construída acelerou de X%/ano para Y%/ano", o que é uma pergunta
   diferente — mais modesta sobre o que mede, mas totalmente respondível sem
   depender de nenhum censo.

**O que não muda:** a arbitragem (a) da seção 1 (documentos do INE em si,
tanto ao vivo quanto via Wayback/mozdata, permanecem nível C por ausência de
licença localizável) continua correta e vigente — o que mudou é que ela deixou
de ser a **única** via para os valores de 2017/2025, não que ela própria tenha
sido revertida. A arbitragem (b) (reassentamentos) e (c) (WorldPop) não são
afetadas por nenhum dos quatro fatos novos e permanecem como emitidas.

> **Nota da revisão de 2026-09-08 (§0'):** o item 4 acima (H1 por ADR 0003)
> segue válido quanto a tirar H1 da dependência de censo, mas precisa da
> reformulação adicional de §0' (taxa de primeira detecção, não estoque) —
> ver "P1/H1" em §0'.

---

## 1. Arbitragem dos três casos remetidos ao auditor

### (a) Documentos do INE via Internet Archive / mozdata — **classificados C**

Fatos: `ine.gov.mz` está fora do ar; os documentos (Quadro 3 do III RGPH 2007,
Quadro 3 do IV RGPH 2017, brochura nacional 2017) foram recuperados via Wayback
com hash conferido; `mozdata.ine.gov.mz` responde 200 mas não expõe termos de
uso legíveis por máquina; **nenhum texto de licença do INE foi localizado em
nenhum domínio, ao vivo ou arquivado**.

Decisão do usuário (2026-09-07) resolve **proveniência**: um documento do INE
servido por Wayback ou mozdata conta como primário — isto elimina a objeção
"vem de agregador". Mas §4.0 tem **dois critérios independentes**: proveniência
primária (regra 4, quem produziu o dado) e licença localizável (regra 1, sob
que termos pode ser usado). A decisão do usuário resolve o primeiro, não o
segundo. Regra 1 é textual e não condicional: "sem licença localizável ⇒ C."
Nenhuma exceção está prevista para "produtor cujo site está fora do ar" ou
"produtor governamental que presumivelmente permite uso público" — presumir
licença a partir da natureza da instituição seria inventar licença, que a
tarefa proíbe explicitamente.

**Veredito: nível C**, para todos os documentos INE (censos 1997/2007/2017,
Censo Agro-Pecuário 2009-10, IAI 2020, IOF 2014/15-2019/20-2022, IPC), tanto
os arquivados via Wayback quanto os catálogos mozdata. A proveniência está
resolvida e registrada; a ausência de licença é o fato que governa a
classificação. Isto vale mesmo para os quadros de 2007/2017 cujo conteúdo
numérico já foi conferido byte a byte contra o documento primário — precisão
de leitura não substitui licença.

> **Nota da revisão (§0.1):** este veredito continua correto **como julgamento
> sobre o documento do INE**. Ele deixou de ser a última palavra sobre os
> *valores* de 2017/2025, que agora têm via A independente (HDX/OCHA, ver §0).
> 1997 e 2007 seguem sem essa segunda via em nível A.

**Consequência declarada, sem eufemismo**: nenhum número populacional do
**documento do INE em si** (1997, 2007, 2017), nem tabulação censitária de
agricultura/renda, sustenta número publicado no núcleo A do app ou do artigo,
por §4.0 regra 1 e pelo critério de qualidade "apenas fontes de nível A
sustentam números publicados" (§10). Isso continua atingindo diretamente as
tabulações desagregadas (agricultura, renda, domicílio) citadas apenas pelo
INE — nenhuma delas tem reprocessador alternativo conhecido. Para os **totais
populacionais por distrito/cidade** especificamente, ver §0: HDX oferece rota
alternativa para 2017 e 2025.

### (b) Literatura de reassentamento — **confirma o quadro do coletor; resta apenas OSM em A**

Classificação mantida: OSM = A; HRW 2013 = B (CC BY-NC-ND, sem redistribuir
derivada); Lillywhite/Kemp/Sturman 2015, Mosca & Selemane 2011, Kirshner &
Power 2015, CIP, Justiça Ambiental = C (sem licença localizável ou paywall);
EIA/RAP de Vale/Riversdale/Jindal = C (não disponíveis publicamente, 404/406).

**O que resta respondível em nível A para a pergunta 3 de §1** ("onde estão,
quanto ocupam, como evoluíram, articulação com a malha urbana"):
- **Onde estão**: parcial. Dois de três núcleos têm nó pontual no OSM (Cateme,
  Mwaladzi); 25 de Setembro não tem geometria localizável no OSM nesta
  verificação. São pontos, não polígonos — não delimitam a área ocupada.
- **Quanto ocupam**: **não respondível em A**. Não há polígono oficial de
  nenhum povoado de reassentamento em fonte A; a área só existe nos EIA/RAP
  (C/indisponíveis) e nas contagens de família do HRW (B). Um polígono
  aproximado poderia ser digitalizado sobre WSF/GHSL/Landsat-Sentinel (A) ao
  redor do ponto OSM, mas isso é reconstrução própria, não um dado de área
  atestado por fonte primária — deve ser rotulado "estimado por
  fotointerpretação", nunca "área do reassentamento" tout court.
- **Como evoluíram (consolidação/abandono/adensamento)**: parcial e indireto.
  WSF Evolution (1985–2015) e GHSL BUILT-S/POP (A) permitem observar a
  evolução do construído num buffer arbitrário ao redor do ponto OSM, mas sem
  o polígono oficial do plano de reassentamento a atribuição causal
  ("isto é o reassentamento, não expansão orgânica adjacente") fica frágil.
- **Articulação com a malha urbana**: respondível em A via OSM (vias) + WSF/
  GHSL, na medida em que o próprio recorte espacial acima permitir.
- **Contagem de famílias (716/289/84, ou a alternativa 1.005/1.365 do próprio
  HRW)**: **não respondível em A**. Fonte é B (HRW); por §4.0 não sustenta
  conclusão nem entra em tabela de resultados. Deve aparecer apenas como
  "validação B" com a divergência interna do próprio relatório (1.005 vs.
  1.365) registrada, não resolvida.

**Síntese**: pergunta 3 é **parcial, degradada a quase puramente geográfico**
em nível A (localização aproximada + evolução do construído num buffer), sem
área oficial nem dimensão populacional/domiciliar em A. **Não afetada pelos
fatos novos desta revisão.**

> **Nota da revisão de 2026-09-08 (§0'):** o componente "como evoluíram" deixou
> de ser puramente indireto para o subitem consolidação/abandono: `docs/ADR/0014`
> removeu a catraca (R2) da série de `reassentamento`, tornando abandono
> observável na série própria pela primeira vez. Ver "P3" em §0'. Os demais
> subitens (quanto ocupam, contagem de famílias) permanecem como aqui emitidos.

### (c) WorldPop / GRID3 — **classificado A**

A página geral do produtor (hub.worldpop.org) declara CC BY 4.0 como licença
padrão de todos os produtos WorldPop, com a exceção nomeada e explícita de
camadas derivadas de OSM/Microsoft Building Footprints/Microsoft Roads (que
seguem ODbL). O item específico "MOZ Population v1.1" no GRID3 Data Hub não
repete esse campo na própria página (`licenseInfo: null` no JSON), mas isso é
lacuna de metadado, não ausência de política — a declaração de licença é do
produtor (WorldPop/GRID3, mesma organização, mesmo domínio de política), feita
em nível de programa, e nenhuma indicação em contrário aparece para este
dataset específico. Diferente do caso INE (onde a busca por qualquer licença,
em qualquer nível — geral ou específico — não encontrou nada), aqui existe
texto de licença explícito do produtor; falta apenas a mesma frase repetida no
metadado JSON de um item.

**Veredito: A**, com nota de que é dado **modelado** (dasimetria WorldPop 2017),
não observado, e que se a camada usada comprovadamente derivar de OSM/MS
Building Footprints a licença efetiva passa a ser ODbL (ainda A, mas com
atribuição/compartilhamento distintos — registrar qual se aplica ao usar).
**Não afetada pelos fatos novos desta revisão** — permanece um ponto de
validação de ordem de grandeza para 2017, agora acompanhado por HDX (também A)
para o mesmo ano e por HDX 2025 (A, modelado) como segundo ponto.

---

## 2. Tabela de fontes por nível (síntese; fragmentos têm o detalhe linha a linha)

### Nível A

| Família | Fonte | Observação |
|---|---|---|
| Imagem | Landsat C2 L2 (USGS), Sentinel-2 L2A (Copernicus) | domínio público / licença Copernicus; via STAC (Planetary Computer + Element84), sem dependência de GEE |
| Construída | WSF Evolution, WSF 2015/2019 (DLR) | CC-BY-4.0; **agora caminho crítico da linha de base 1997–2005 (ADR 0003)**; **também monotônico por construção — ver §0'/ADR 0008 emenda**; **Fase 3: 5 tiles adicionais das capitais de controle, mesma licença — ver §0''** |
| Construída | GHSL BUILT-S/BUILT-V/POP/SMOD R2023A (JRC) | CC-BY-4.0; observado até 2020 |
| Construída | GHSL R2025 (projeções 2025–2100) | CC-BY-4.0; **modelado/extrapolado**, não observado |
| Construída | Google Open Buildings v3, Microsoft Global Building Footprints | CC-BY-4.0/ODbL; CDLA Permissive 2.0 |
| Construída/Reassent. | OpenStreetMap (Geofabrik) | ODbL 1.0 |
| Construída | Maus et al. 2020/2022 — Global-scale Mining Polygons v1/v2 | CC-BY-SA-4.0 |
| Demográfica | HDX COD-PS, HDX COD-AB Moçambique | CC BY-IGO; **vintages confirmados: 2017 (observado), 2023/2024/2025 (modelado/projeção INE)**; limites com "ajustes não oficiais", revisão INE só em 2027 |
| Demográfica | HDX COD-PS — **valor específico Cidade de Tete/Moatize 2017 e 2025** | **novo nesta revisão**: 2017 = 307.338/260.843 (observado, idêntico ao documento INE via Wayback); 2025 = 460.248/349.103 (modelado, projeção INE; risco de circularidade se usado para testar H4 — ver §0.2) |
| Demográfica | WorldPop / GRID3 MOZ v1.1 | CC-BY 4.0 (política geral do produtor); ver arbitragem (c); **modelado**, ano 2017 |
| Demográfica | DHS — relatórios finais / STATcompiler | acesso aberto sem registro para consulta agregada; ODbL no Spatial Data Repository |
| Econômico | DMSP-OLS, VIIRS DNB (EOG) | domínio público **quanto ao conteúdo; ver §0'' — acesso direto ao VIIRS DNB rebaixado a B, DMSP-OLS excluído (C) por bloqueio de acesso em 2026-09-08** |
| Econômico | Harmonized DMSP-VIIRS — **corrigido em §0''**: o produto efetivamente coletado é **NPP-VIIRS-like (Chen, Z., Yu, B. et al. 2021), Harvard Dataverse, DOI 10.7910/DVN/YGIVCD, CC0 1.0**, não "Li et al. 2020" (produto distinto, figshare) | CC0 1.0; **descontinuidade não resolvida entre 2020 e 2022 (radiância máx. 70,4→49,9 na AOI de Tete) — ver §0'' | única série de luz de nível A restante após a exclusão dos itens acima |
| Econômico | World Bank Pink Sheet | domínio público |
| Econômico | Global Coal Mine Tracker (GEM) | CC-BY 4.0; acesso por formulário, sem aprovação |
| Agricultura | GLAD Global Cropland, ESA WorldCover, CGLS-LC100, ESRI/IO 10m LULC | CC-BY 4.0 / licença Copernicus; **agora usadas como referência que reprova `cultivo_sequeiro` — ver §0'/ADR 0012** |
| Agricultura | Copernicus DEM GLO-30 (via bucket AWS, não OpenTopography) | licença Copernicus |
| Agricultura | HydroRIVERS v1.0 | licença própria HydroSHEDS (uso livre com atribuição; não CC0) |
| Reassentamento | OpenStreetMap (nós Cateme, Mwaladzi) | ODbL 1.0; geometria apenas, sem atributos de família |
| Demográfica/Geometria | HDX COD-AB Moçambique (`moz_admin_boundaries.geojson.zip`) | **novo em §0''**: CC BY-IGO 3.0; ADM0–3, P-codes das 5 capitais de controle + Tete/Moatize |

### Nível B (validação opcional, nunca núcleo)

| Fonte | Motivo |
|---|---|
| IPUMS International (amostras 10%) | uso restrito a pesquisa/ensino, proíbe redistribuição do bruto |
| DHS — microdados 1997/2003/2011/2015 | requer aprovação de projeto, não redistribuível |
| Human Rights Watch (2013) | CC BY-NC-ND 3.0 — proíbe obra derivada |
| Dynamic World (Google/WRI) | único acesso real é GEE; sem STAC público (404 no Planetary Computer) |
| Planet NICFI | não comercial, proíbe redistribuição do bruto; **e, em 2026, programa descontinuado sem sucessor** — inacessível na prática |
| OpenTopography (com chave de API pessoal) | não é acesso anônimo; via primária A é o bucket Copernicus DEM na AWS |
| **UNSD Demographic Yearbook 2007, Tabela 8** (novo nesta revisão) | confirma Cidade de Tete 1997 = 101.984 exatamente; licença ONU proíbe redistribuição e obra derivada sem autorização escrita — válido só como validação, não como fonte publicável |
| **VIIRS VNL V2 (EOG, `eogdata.mines.edu`) — novo em §0''** | rebaixada de A: todo download testado exige login OAuth (`eogauth.mines.edu`); não é acesso anônimo nem cadastro trivial |

### Nível C (excluído; nunca no núcleo)

| Fonte | Motivo |
|---|---|
| INE — Censo 1997 (II RGPH), brochura provincial de Tete | sem licença localizável (proveniência primária é irrelevante aqui: conteúdo numérico também nunca foi arquivado) |
| INE — Censo 2007 (III RGPH), Quadro 3 Tete | sem licença localizável na página do produtor, apesar de proveniência primária confirmada |
| INE — Censo 2017 (IV RGPH), Quadro 3 Tete + brochura nacional | idem — **mas ver §0: o mesmo valor numérico tem via A independente via HDX** |
| INE — mozdata (catálogos Censo 2007/2017, Censo Agro-Pecuário 2009-10, IAI 2020, IOF 2014/15-2022) | idem; adicionalmente, fluxo de aprovação de "get-microdata" não verificado |
| INE — Índice de Preços ao Consumidor (Tete) | servidor inacessível nesta verificação; licença nunca localizada |
| Lillywhite, Kemp & Sturman (2015) | nenhuma licença localizável na página do produtor (UQ/CSRM); cópia Oxfam bloqueada (403) |
| Mosca & Selemane (2011), CIP | "todos os direitos reservados" no rodapé do site produtor |
| Kirshner & Power (2015), Geoforum | paywall Elsevier; via aberta (Unpaywall/Durham) retornou 403, não confirmada |
| CIP — relatórios diversos | "todos os direitos reservados" |
| Justiça Ambiental (JA!) | licença não localizada |
| EIA/RAP — Vale (Moatize) | não disponível publicamente (404) |
| EIA/RAP — Riversdale/Rio Tinto (Benga) | não localizado |
| EIA/RAP — Jindal (Tete) | não disponível (406) / não localizado |
| **DMSP-OLS estável (NOAA/NCEI) — novo em §0''** | URL de CLAUDE.md §4.4 responde HTTP 404; página sucessora (EOG) exige login OAuth; nenhuma licença localizável no domínio que efetivamente serve o dado hoje |

### Via não esgotada (nem A/B/C — indisponibilidade externa, distinta de "não existe")

| Fonte | Motivo |
|---|---|
| CIESIN/SEDAC — GPWv3 National Identifier Grid, GPWv4 Population Count (input data por distrito, Moçambique) | `sedac.ciesin.columbia.edu` fora do ar (timeout, código `000`, não 404) em todas as tentativas em 2026-09-07; era a via mais promissora para 1997/2007 por distrito porque o GPW publica os insumos administrativos de origem. **Reexecutar quando o domínio voltar** — não registrar como "dado inexistente". |

---

## 3. Matriz pergunta/hipótese × suficiência em nível A (revista em 2026-09-07; **qualificada em 2026-09-08, ver §0'/§0''**)

| # | Pergunta/Hipótese (§1) | Veredito (original) | Veredito (revisto 2026-09-07) | Veredito (qualificado 2026-09-08) | O que mudou / o que falta |
|---|---|---|---|---|---|
| P1 | Tendência pré-projetos 1997–2005 | PARCIAL | RESPONDÍVEL (reformulada por área, ADR 0003) | **TESTÁVEL EM A, restrito a taxa de primeira detecção** | WSF Evolution é monotônico por construção (emenda ADR 0008); estoque não é testável por nenhuma fonte disponível, só a taxa anual de primeira detecção. Ver §0'. |
| P2 | Implantação e boom 2005–2015 | PARCIAL | PARCIAL, com endpoint melhor ancorado | **PARCIAL — adicionalmente, o par 2015–2020 da série própria está contaminado** (ADR 0013) e não sustenta magnitude de efeito | Área/forma construída testável em A, mas 2015 tem inflação de rotulagem de ~15 km²; não usar esse par para medir a saída do boom. |
| P3 | Reassentamentos: onde, quanto ocupam, evolução, articulação | PARCIAL, degradado | Inalterado | **PARCIAL, melhorado no subitem "evolução"**: abandono agora observável (R2 removido, ADR 0014) | Polígono oficial e contagem de famílias seguem ausentes de A/fora de A. |
| P4 | Forma de urbanização (compacta/dispersa, infill/borda/leapfrog, eixos) | RESPONDÍVEL | Inalterado — RESPONDÍVEL | **RESPONDÍVEL COM RESSALVA DE CHURN** (31–54 % entre anos-âncora, ADR 0013) | Área agregada por tipologia OK; atribuição pixel a pixel carrega incerteza de identidade a declarar. |
| P5 | Crescimento econômico local vs. ciclos do carvão | RESPONDÍVEL | Inalterado — RESPONDÍVEL | **RESPONDÍVEL, com aviso adicional de versão do produto de luz pós-2020 (§0'')** | Método (luzes) não afetado pelos ADRs 0012–0014; a série de luz disponível mudou de fonte (Chen/Yu, não Li) e carrega descontinuidade 2020→2022 não resolvida. |
| P6 | Bust e transição 2015–2025 | PARCIAL (sem âncora demográfica pós-2017) | PARCIAL, melhorado — respondível com ressalva de selo | **PARCIAL — adicionalmente, não usar o par 2015–2020 da série própria como base do efeito de bust** (ADR 0013); usar luzes como série primária pós-2015, **com o aviso de versão de produto de §0'' na quebra de 2022** | Ver P2. Luzes noturnas (não catraca) recomendadas como série primária depois de 2015, mas só a série Chen/Yu está em A, com descontinuidade não auditável entre 2020–2022. |
| P7 | Cenários pós-2025 (2035/2040) | RESPONDÍVEL COM RESSALVA | Melhorado — base populacional mais robusta | **Inalterado quanto ao componente demográfico**; componente de área herda as ressalvas de P1/P2/P6 | Extrapolação sobre extrapolação permanece; agora também herda a ressalva de taxa-vs-estoque de H1. |
| P8 | Agricultura urbana e periurbana | PARCIAL | Inalterado — PARCIAL | **PARCIAL, restrito a localização (várzea) e a `cultivo_irrigado` com ressalva** — "quanto ocupam" e "como evoluíram" NÃO respondíveis | `cultivo_sequeiro` reprovado (kappa −0,065, Jaccard 0,001–0,002); ver §0'. |
| H1 | Aceleração 4%→7%/ano (1997→2007→2017), reformulada por ADR 0003 em termos de área construída | NÃO TESTÁVEL EM A | TESTÁVEL EM A (reformulada) | **TESTÁVEL EM A, mas só como taxa de primeira detecção, não como estoque** | Emenda ADR 0008 (2026-09-08): WSF também monotônico. Nenhuma fonte dá estoque sem catraca imposta. |
| H2 | Expansão dispersa/borda com leapfrog | RESPONDÍVEL | Inalterado — RESPONDÍVEL | **RESPONDÍVEL COM RESSALVA DE CHURN** (mesma ressalva de P4) | — |
| H3 | Pegada industrial cresce mais rápido 2010–2015, estabiliza pós-2016; mancha urbana por inércia demográfica | PARCIAL | PARCIAL, com evidência adicional fraca | **PARCIAL, componente industrial melhora** (R2 removido de `industrial`, ADR 0014 — reabilitação de cava agora detectável); componente demográfico inalterado | — |
| H4 | Luzes descolam da população pós-2016 | NÃO TESTÁVEL EM A | PARCIAL, com risco de circularidade — não sustenta conclusão sozinha | **PARCIAL, risco de circularidade duplo, agora triplo (§0'')** (lado população: projeção INE 2025; lado área: catraca R2 de `urbano`; lado luz: descontinuidade de versão do produto 2020→2022 não auditável) | Usar GHSL observado (não R2025) ou `estoque_sustentado_pelo_ano_km2` para o lado da área; nunca a série R2 publicada. A série de luz disponível (Chen/Yu) não permite verificação independente da conciliação DMSP↔VIIRS nem da descontinuidade 2020–2022. Ver ADR 0013 "Não pode" e §0''. |
| H5 | Conversão cropland→construído concentrada na implantação/boom; persistência em várzeas | RESPONDÍVEL, com ressalva de fenologia | Inalterado | **SUSTENTADA FRACAMENTE** — só o componente de localização relativa em várzea (enriquecimento 2–3× de `cultivo_irrigado`, 4 de 6 anos), nunca magnitude de área/conversão | `cultivo_sequeiro`: acurácia 0,000, kappa −0,065 (ADR 0012), não corrigido pela raiz (ADR 0014). Ver §0'. |
| H6 | Agricultura urbana como amortecedor pós-2016 (sobretudo reassentados) | PARCIAL | Inalterado — PARCIAL | **SEM RESPOSTA** — motivo mudou: não é (só) lacuna domiciliar (INE=C), é que a série de área de cultivo tem kappa negativo e não mede cropland | Ver §0'. |

---

## 4. Veredito (revisto em 2026-09-07; qualificado em 2026-09-08 — ver §0'/§0'')

**CONJUNTO A INSUFICIENTE — por dois motivos independentes, mais um risco declarado
sobre a série de luz.** (i) Lacunas de licença/proveniência: 1997/2007 sem âncora
demográfica em A; tabulações domiciliares/agrícolas do INE fechadas ao núcleo A
(inalterado desde 2026-09-07). (ii) **Lacunas de desempenho de classificação, medidas
em 2026-09-08** (`docs/ADR/0012`, `0013`, `0014`): `cultivo_sequeiro` não separa
cultivo de vegetação natural (kappa −0,065), o que impede H5 de sustentar
magnitude e torna H6 e a maior parte de P8 SEM RESPOSTA; e nenhuma fonte
disponível de área construída (classificação própria com R2, ou WSF Evolution)
fornece estoque sem monotonicidade imposta, o que restringe H1/P1 a taxa de
primeira detecção e proíbe usar o par 2015–2020 como base de efeito para P2/P6,
e a série R2 de `urbano` como lado da área em H4. (iii) **Risco declarado desde
2026-09-08, tarde (§0''):** a única série de luz de nível A hoje disponível
(Chen/Yu, NPP-VIIRS-like, Harvard Dataverse) resolve a conciliação DMSP↔VIIRS
dentro de um modelo de terceiros não auditável, e apresenta uma descontinuidade
de radiância (70,4→49,9 entre 2020 e 2022) coincidente com um reprocessamento
documentado do produto na mesma janela — nenhuma fonte A permite hoje verificação
independente dessa descontinuidade, o que qualifica qualquer quebra estimada em
2022 (P6, H4) até que uma segunda via seja obtida.

O que a revisão de 2026-09-07 mudava, em síntese, permanece registrado abaixo
sem alteração: o veredito original tratava 1997/2007/2017 como um bloco único
bloqueado pela reclassificação C dos documentos do INE. Isso permanece correto
para os **documentos**, mas dois fatos o superam parcialmente: (i) HDX/OCHA (CC
BY-IGO, nível A) fornece o mesmo valor de 2017 por via independente, e agora
também um ponto de 2025 (modelado); (ii) ADR 0003 tira a fase de linha de base
(1997–2005 e H1) da dependência de censo por completo, ao reformulá-la em área
construída (WSF Evolution, nível A) — **reformulação que a emenda de 2026-09-08
ao ADR 0008 restringe outra vez, à taxa de primeira detecção (ver §0')**. O que
**não** muda: 1997 e 2007 seguem sem âncora populacional em A; tabulações
censitárias sobre agricultura/renda/domicílio permanecem C sem reprocessador
alternativo; a família de reassentamento (P3) melhora num subitem (ver §0') mas
segue sem polígono oficial nem contagem de famílias em A.

**Condição de abertura por módulo (revista):**

1. **Módulos independentes de censo e de classificação de cultivo** — imagem,
   forma urbana (WSF/GHSL/OSM/Google-MS buildings) **como taxa, não estoque**,
   luzes noturnas, mapeamento de várzea (geometria, não classificação
   espectral): **abrem sem restrição adicional**, fonte A completa.
2. **Módulo demográfico — extremidade 2017/2025 (inalterado desde
   2026-09-07)**: abre sob as três obrigações já registradas na seção 0
   (citar HDX/OCHA, selo observado/modelado, nunca usar 2025 como prova
   independente de H4).
3. **Módulo demográfico — extremidade 1997/2007 (inalterado, bloqueado)**:
   permanece fechado ao núcleo A.
4. **Reassentamentos (P3)**: publicar localização aproximada, evolução do
   buffer construído (agora incluindo abandono, não catraca) e articulação
   viária. Toda contagem de famílias e toda leitura de área oficial carrega o
   selo "validação B — HRW 2013".
5. **Tabulações domiciliares/agrícolas do INE (P8/H6)**: fechadas ao núcleo A
   — inalterado. **Adicionalmente, desde 2026-09-08**: mesmo a dimensão física
   (área cultivada) de P8/H6 está fechada — não por licença, por desempenho de
   classificação (ADR 0012/0014). Publicável apenas: localização de várzea
   (geometria) e `cultivo_irrigado` com ressalva de acurácia (IC95 amplo).
   `cultivo_sequeiro` publica-se só como camada "candidata", nunca como
   "cultivo confirmado" (ADR 0012, item 3).
6. **H1/P1 (reformulada)**: abre como teste em **taxa de primeira detecção**
   de área construída (WSF Evolution), não em estoque nem em população. As
   quebras de 2005/2011 são estimáveis sobre essa taxa; nenhuma quebra é
   estimável sobre o acumulado publicado (série própria ou WSF).
7. `pipeline/00_fetch/fetch_wsf_evolution.py` permanece caminho crítico da
   Fase 1 (ADR 0003), agora lido como fonte de taxa, não de estoque.
8. **Placebos obrigatórios para toda quebra estimada em §5.4 (ampliado)**: além
   dos placebos espacial e temporal já previstos, a quebra sobre mediana de
   observações por pixel (ADR 0008) e a quebra sobre a fração da AOI com
   NDVI(seca) ≥ mediana×1,30 (ADR 0013/0014, quarto placebo). Se a quebra
   aparecer também nesses controles, é artefato de sensor/rotulagem, não
   tratamento. **Desde §0'': toda quebra estimada em 2020–2022 sobre a série
   de luz carrega adicionalmente o aviso de descontinuidade de versão do
   produto, não substituível por nenhum dos quatro placebos acima (nenhum
   deles testa "mudança de versão do produtor").**
9. **Série de luzes noturnas (novo, §0'')**: o núcleo A é exclusivamente o
   produto Chen/Yu (NPP-VIIRS-like, Harvard Dataverse, CC0 1.0, DOI
   10.7910/DVN/YGIVCD) — **não** "Li et al. 2020" como registrado em
   `CLAUDE.md` §4.4, que descreve um produto diferente, não coletado. VIIRS
   VNL direto (EOG) é nível B (login OAuth obrigatório); DMSP-OLS estável
   (NOAA/NCEI) está excluído, nível C (página 404, sucessora bloqueada).
   `CLAUDE.md` §4.4 precisa de correção editorial para refletir isso.

Nenhuma âncora de §8 deste repositório pode ser citada diretamente a partir do
documento do INE no núcleo A. Os valores 307.338 (2017, Tete) e 260.843 (2017,
Moatize) **podem** ser citados no núcleo A **desde que a citação aponte para o
HDX COD-PS/OCHA**, não para o INE diretamente — o INE permanece a "fonte
declarada" dentro dos metadados do HDX, mencionável em prosa, mas não a fonte
licenciada do dado. 155.870 (2007) e 101.984/109.103 (1997) continuam sem
nenhuma via de nível A e não devem ser citados como número do núcleo,
independentemente de quantas vezes tenham sido confirmados byte a byte contra
o documento primário.

Nenhum número de área de `cultivo_sequeiro`, e nenhuma magnitude de conversão
cropland→construído ou de área cultivada amortecedora do bust (H5/H6), deve
ser citado como número do núcleo A do app ou do artigo — apenas a leitura
relativa e qualificada registrada em §0'.

Nenhuma quebra de nível ou inclinação estimada sobre a série de luzes noturnas
entre 2020 e 2022 (P6, H4) deve ser publicada sem o aviso explícito de que a
descontinuidade medida (radiância máxima 70,4→49,9 na AOI de Tete) coincide com
um reprocessamento documentado do produto Chen/Yu nessa mesma janela, e que
nenhuma fonte de nível A permite hoje verificar essa descontinuidade de forma
independente (§0'').

**Veredito global: CONJUNTO A INSUFICIENTE.**
