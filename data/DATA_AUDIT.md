# DATA_AUDIT.md — Fase 0', Portão de Auditoria (§4.0, regra 5)

Consolidado em 2026-09-07 a partir de `data/LICENSES.md`, `PROVENANCE.md` e dos
fragmentos por família em `data/licenses_parts/` e `data/provenance_parts/`.
Este documento resolve toda linha `pendente_auditoria` e emite o veredito de
abertura da Fase 1.

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
   que o valor é contagem residente **sem** o ajuste de omissão de 3,7–3,8%
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
| Construída | WSF Evolution, WSF 2015/2019 (DLR) | CC-BY-4.0; **agora caminho crítico da linha de base 1997–2005 (ADR 0003)** |
| Construída | GHSL BUILT-S/BUILT-V/POP/SMOD R2023A (JRC) | CC-BY-4.0; observado até 2020 |
| Construída | GHSL R2025 (projeções 2025–2100) | CC-BY-4.0; **modelado/extrapolado**, não observado |
| Construída | Google Open Buildings v3, Microsoft Global Building Footprints | CC-BY-4.0/ODbL; CDLA Permissive 2.0 |
| Construída/Reassent. | OpenStreetMap (Geofabrik) | ODbL 1.0 |
| Construída | Maus et al. 2020/2022 — Global-scale Mining Polygons v1/v2 | CC-BY-SA-4.0 |
| Demográfica | HDX COD-PS, HDX COD-AB Moçambique | CC BY-IGO; **vintages confirmados: 2017 (observado), 2023/2024/2025 (modelado/projeção INE)**; limites com "ajustes não oficiais", revisão INE só em 2027 |
| Demográfica | HDX COD-PS — **valor específico Cidade de Tete/Moatize 2017 e 2025** | **novo nesta revisão**: 2017 = 307.338/260.843 (observado, idêntico ao documento INE via Wayback); 2025 = 460.248/349.103 (modelado, projeção INE; risco de circularidade se usado para testar H4 — ver §0.2) |
| Demográfica | WorldPop / GRID3 MOZ v1.1 | CC-BY 4.0 (política geral do produtor); ver arbitragem (c); **modelado**, ano 2017 |
| Demográfica | DHS — relatórios finais / STATcompiler | acesso aberto sem registro para consulta agregada; ODbL no Spatial Data Repository |
| Econômico | DMSP-OLS, VIIRS DNB (EOG) | domínio público |
| Econômico | Harmonized DMSP-VIIRS (Li et al. 2020) | CC-BY 4.0 (nota: inconsistência interna entre fragmentos sobre exigência de cadastro no figshare — licença é aberta; tratado como A, registrar a inconsistência) |
| Econômico | World Bank Pink Sheet | domínio público |
| Econômico | Global Coal Mine Tracker (GEM) | CC-BY 4.0; acesso por formulário, sem aprovação |
| Agricultura | GLAD Global Cropland, ESA WorldCover, CGLS-LC100, ESRI/IO 10m LULC | CC-BY 4.0 / licença Copernicus |
| Agricultura | Copernicus DEM GLO-30 (via bucket AWS, não OpenTopography) | licença Copernicus |
| Agricultura | HydroRIVERS v1.0 | licença própria HydroSHEDS (uso livre com atribuição; não CC0) |
| Reassentamento | OpenStreetMap (nós Cateme, Mwaladzi) | ODbL 1.0; geometria apenas, sem atributos de família |

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

### Via não esgotada (nem A/B/C — indisponibilidade externa, distinta de "não existe")

| Fonte | Motivo |
|---|---|
| CIESIN/SEDAC — GPWv3 National Identifier Grid, GPWv4 Population Count (input data por distrito, Moçambique) | `sedac.ciesin.columbia.edu` fora do ar (timeout, código `000`, não 404) em todas as tentativas em 2026-09-07; era a via mais promissora para 1997/2007 por distrito porque o GPW publica os insumos administrativos de origem. **Reexecutar quando o domínio voltar** — não registrar como "dado inexistente". |

---

## 3. Matriz pergunta/hipótese × suficiência em nível A (revista em 2026-09-07)

| # | Pergunta/Hipótese (§1) | Veredito (original) | Veredito (revisto) | O que mudou / o que falta |
|---|---|---|---|---|
| P1 | Tendência pré-projetos 1997–2005 | PARCIAL | **RESPONDÍVEL (reformulada por área, ADR 0003)** | Deixa de depender de população. WSF Evolution (A, 1985–2005, 21 anos) mede a mancha construída pré-tratamento com resolução superior a 3 censos. A dimensão populacional específica (habitantes) continua sem 1997/2007 em A — mas essa dimensão não é mais o que a pergunta exige na formulação aceita. |
| P2 | Implantação e boom 2005–2015 | PARCIAL | **PARCIAL, com endpoint melhor ancorado** | Área/forma construída e pegada industrial testáveis em A (inalterado). HDX 2017 (A, observado) dá um ponto populacional logo após o boom, útil como referência de saída de fase — mas o boom em si (2005–2015) segue sem âncora populacional intermediária em A. Reassentamento: polígonos oficiais continuam ausentes de A. |
| P3 | Reassentamentos: onde, quanto ocupam, evolução, articulação | PARCIAL, degradado | **Inalterado** | Nenhum dos 4 fatos novos toca esta família (arbitragem (b) não afetada). |
| P4 | Forma de urbanização (compacta/dispersa, infill/borda/leapfrog, eixos) | RESPONDÍVEL | **Inalterado — RESPONDÍVEL** | — |
| P5 | Crescimento econômico local vs. ciclos do carvão | RESPONDÍVEL | **Inalterado — RESPONDÍVEL** | — |
| P6 | Bust e transição 2015–2025 | PARCIAL (sem âncora demográfica pós-2017) | **PARCIAL, melhorado — respondível com ressalva de selo** | HDX 2025 (A, **modelado**) dá um segundo ponto populacional após 2017. Dois pontos (1 observado + 1 modelado, 8 anos de intervalo) permitem situar ordem de grandeza da trajetória, mas não caracterizam "desaceleração/estagnação/reconversão" com a granularidade que a pergunta pede — isso continua vindo dos proxies de forma construída e luzes (A, já respondível). Selo `modelado` deve aparecer em qualquer gráfico/tabela que use o ponto 2025. |
| P7 | Cenários pós-2025 (2035/2040) | RESPONDÍVEL COM RESSALVA | **Melhorado — base populacional mais robusta** | Agora há dois pontos A explícitos (HDX 2017 observado + HDX 2025 modelado, mais WorldPop/GRID3 2017 modelado) para ancorar o componente demográfico do cenário, em vez de um único corte. Ainda é extrapolação sobre extrapolação no trecho 2025→2035/2040 — declarar isso explicitamente. |
| P8 | Agricultura urbana e periurbana | PARCIAL | **Inalterado — PARCIAL** | Tabulações censitárias de agricultura/renda continuam exclusivas do INE (documento), sem reprocessador alternativo identificado — diferente da população total, que tinha o HDX como segunda via. Mapeamento de cultivo/várzea segue respondível (já era). |
| H1 | Aceleração 4%→7%/ano (1997→2007→2017), **reformulada por ADR 0003 em termos de área construída** | NÃO TESTÁVEL EM A | **TESTÁVEL EM A (reformulada)** | WSF Evolution dá 19 observações anuais (1997–2015) em nível A. A formulação original em habitantes/ano permanece não testável em A (1997/2007 ausentes) e deve ser abandonada, não citada como resultado — apenas a formulação em área construída sustenta conclusão do núcleo. |
| H2 | Expansão dispersa/borda com leapfrog | RESPONDÍVEL | **Inalterado — RESPONDÍVEL** | — |
| H3 | Pegada industrial cresce mais rápido 2010–2015, estabiliza pós-2016; mancha urbana por inércia demográfica | PARCIAL | **PARCIAL, com evidência adicional fraca** | Componente de pegada industrial: inalterado, testável em A. Componente "inércia demográfica": HDX 2017/2025 dá dois pontos, mas 2025 é modelado — insuficiente para confirmar "crescimento por inércia" de forma robusta; tratar como leitura exploratória, apoiada principalmente pela série de área construída (GHSL/imagem própria), que é observada e mais densa. |
| H4 | Luzes descolam da população pós-2016 | NÃO TESTÁVEL EM A | **PARCIAL, com risco de circularidade — não sustenta conclusão sozinha** | Agora há dois pontos populacionais A pós-2016 (2017 observado, 2025 modelado), tecnicamente suficientes para calcular uma taxa. Mas a projeção INE 2025 provavelmente assume crescimento geométrico contínuo, o que tende a **produzir** o padrão "população sobe, luz estagna" independentemente da realidade — ver §0.2. Uso permitido apenas como leitura complementar rotulada, com o proxy de área construída/edificações (GHSL, observado) como evidência principal, não a população modelada. |
| H5 | Conversão cropland→construído concentrada na implantação/boom; persistência em várzeas | RESPONDÍVEL, com ressalva de fenologia | **Inalterado** | — |
| H6 | Agricultura urbana como amortecedor pós-2016 (sobretudo reassentados) | PARCIAL | **Inalterado — PARCIAL** | Dimensão domiciliar segue dependente de Censo/IOF (C) e literatura B/C; nenhum dos 4 fatos novos abre via alternativa para isso. |

---

## 4. Veredito (revisto em 2026-09-07)

**CONJUNTO A INSUFICIENTE — mas o bloqueio se reduziu de "pilar demográfico
inteiro" para "extremidade pré-2017 do pilar demográfico + tabulações
domiciliares/agrícolas do INE". Fase 1 abre para mais módulos do que na
emissão original, sob condições revistas abaixo.**

O que a revisão muda, em síntese: o veredito original tratava 1997/2007/2017
como um bloco único bloqueado pela reclassificação C dos documentos do INE.
Isso permanece correto para os **documentos**, mas dois fatos o superam
parcialmente: (i) HDX/OCHA (CC BY-IGO, nível A) fornece o mesmo valor de 2017
por via independente, e agora também um ponto de 2025 (modelado); (ii) ADR
0003 tira a fase de linha de base (1997–2005 e H1) da dependência de censo por
completo, ao reformulá-la em área construída (WSF Evolution, nível A). O que
**não** muda: 1997 e 2007 seguem sem âncora populacional em A; tabulações
censitárias sobre agricultura/renda/domicílio permanecem C sem reprocessador
alternativo; a família de reassentamento (P3) e a dimensão domiciliar de H6
permanecem no mesmo estado.

**Condição de abertura por módulo:**

1. **Módulos independentes de censo (inalterado)** — imagem, forma urbana
   (WSF/GHSL/OSM/Google-MS buildings), luzes noturnas, mapeamento de
   cultivo/várzea (P4, P5, H2, H5, e agora também **P1/H1** via ADR 0003):
   **abrem sem restrição**, fonte A completa.
2. **Módulo demográfico — extremidade 2017/2025 (novo, parcialmente
   desbloqueado)**: **abre**, usando HDX COD-PS como fonte primária de nível A
   para Cidade de Tete e Moatize em 2017 (observado) e 2025 (modelado), com
   três obrigações: (a) citar o reprocessador (OCHA/HDX FIS), não o documento
   INE, quando o número vier apenas de HDX; (b) selo `observado`/`modelado`
   obrigatório e visível em toda figura/tabela que use o ponto de 2025; (c)
   nunca usar o ponto de 2025 como evidência independente de H4 (descolamento
   luz-população) sem a ressalva de circularidade de §0.2 — a evidência
   principal de H4 continua sendo a série de área/edificações observada.
3. **Módulo demográfico — extremidade 1997/2007 (inalterado, bloqueado)**:
   permanece fechado ao núcleo A. UNSD (B) confirma 101.984 (Tete, 1997) só
   para validação rotulada; Moatize 1997 e ambos os valores de 2007 seguem sem
   nenhuma via A ou B identificada. CIESIN/SEDAC continua como via não
   esgotada (servidor fora do ar) — reexecutar antes de declarar
   definitivamente indisponível.
4. **Reassentamentos (P3, inalterado)**: publicar apenas o que a arbitragem
   (b) permite — localização aproximada, evolução do buffer construído,
   articulação viária. Toda contagem de famílias e toda leitura de área
   oficial carrega o selo "validação B — HRW 2013", nunca número definitivo.
5. **Tabulações domiciliares/agrícolas do INE (P8/H6, inalterado)**: seguem
   fechadas ao núcleo A — nenhum reprocessador alternativo foi identificado
   para essas tabulações específicas (diferente dos totais populacionais, que
   têm o HDX). A série física de cultivo/várzea (GLAD/ESRI-IO/WorldCover/DEM)
   permanece respondível e sustenta H5 integralmente.
6. **H1 (reformulada) e P1**: abrem de imediato como testes em área
   construída. A formulação original em população/ano não deve aparecer no
   núcleo A do artigo/app sob nenhuma circunstância — nem como "aproximação",
   nem com selo B — porque nenhuma via B ou A cobre 1997 com granularidade
   distrital confiável (UNSD só cobre "city proper" de Tete, não Moatize, e é
   B).
7. `pipeline/00_fetch/fetch_wsf_evolution.py` passa de opcional a **caminho
   crítico** da Fase 1 (confirmado por ADR 0003) — deve deixar de ser um
   stub de deferimento ao GEE/STAC e obter o dado diretamente do DLR.

Nenhuma âncora de §8 deste repositório pode ser citada diretamente a partir do
documento do INE no núcleo A. Os valores 307.338 (2017, Tete) e 260.843 (2017,
Moatize) **podem** ser citados no núcleo A **desde que a citação aponte para o
HDX COD-PS/OCHA**, não para o INE diretamente — o INE permanece a "fonte
declarada" dentro dos metadados do HDX, mencionável em prosa, mas não a fonte
licenciada do dado. 155.870 (2007) e 101.984/109.103 (1997) continuam sem
nenhuma via de nível A e não devem ser citados como número do núcleo,
independentemente de quantas vezes tenham sido confirmados byte a byte contra
o documento primário.
