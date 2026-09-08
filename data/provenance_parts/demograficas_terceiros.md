# PROVENANCE — Demográficas via reprocessadores institucionais (Fase 0', tarefa adicional)

Fragmento novo, paralelo a `demograficas.md` (fechado). Registra, para cada fonte
candidata a reprocessador institucional (§ distinção do prompt desta tarefa): URL
exata testada, código HTTP, data de acesso, o que foi efetivamente lido, e se os
valores de §8 (101.984 / 109.103 em 1997; 155.870 / 215.092 em 2007; 307.338 / 260.843
em 2017) foram confirmados, divergiram, ou não foram encontrados.

Todas as linhas seguem `PENDENTE` até verificação efetiva (regra "grave incrementalmente").

## 1. CIESIN GPWv3 — National Identifier Grid / documentação Moçambique
Status: NÃO DISPONÍVEL — servidor inacessível.
- URL testada: https://sedac.ciesin.columbia.edu/data/set/gpw-v3-national-identifier-grid
- `curl -m 20 -L -o /dev/null -w '%{http_code}'` retornou `000` (exit 28, timeout) em duas
  tentativas em 2026-09-07. `curl -sI -m 20 https://sedac.ciesin.columbia.edu` também
  falhou (mesmo domínio raiz inacessível).
- Motivo exato: timeout de conexão — não é 404, não é paywall; o servidor não respondeu
  dentro de 20s em nenhuma tentativa desta rodada.
- Não foi possível confirmar se GPWv3 traz dados de entrada por distrito para Moçambique
  1997/2000, nem a licença. Registrado como não disponível, não como C — reavaliar em
  execução futura com o domínio no ar.

## 2. CIESIN GPWv4 — Population Count / Input Data Country-Level, Mozambique
Status: NÃO DISPONÍVEL — mesma falha do item 1.
- URL testada: https://sedac.ciesin.columbia.edu/data/set/gpw-v4-population-count-rev11
- `curl -m 20 -L -o /dev/null -w '%{http_code}'` → `000` (timeout, exit 28), 2026-09-07.
- sedac.ciesin.columbia.edu inteiro inacessível nesta rodada; não confirmável.

## 3. UNSD Demographic Yearbook 2007 — Tabela 8, censo de 1997
Status: VERIFICADO — CONFIRMA a âncora de Tete 1997 (101.984), via reprocessador institucional.
- URL: https://unstats.un.org/unsd/demographic/products/dyb/dyb2007/Table08.xls → HTTP 200.
- Espelhado em `data/raw/unsd_dyb2007_table08_capital_cities.xls` (2.813.440 bytes),
  com `.sha256` e `.meta.json`.
- Tabela 8 "Population of capital cities and cities of 100.000 or more inhabitants:
  latest available year, 1988-2007". Bloco "Mozambique", subcabeçalho "1 VIII 1997
  (CDFC)" (censo de facto, 1 de agosto de 1997): linha "Tete" = 101.984 (city proper,
  ambos os sexos). Lido diretamente do arquivo com `xlrd` (planilha "Data", linha 214).
- Também testada a edição DYB2000 (Table08.xls, planilha "tables"): só lista Maputo
  para 1997 (1.015.300 na tabela de urban agglomeration da edição 2000, célula
  diferente da de 2007 — a UNSD atualiza retroativamente conforme países submetem
  dados); Tete não aparece na edição 2000, só na de 2007. Não gravado em disco por
  não conter dado relevante ao escopo desta tarefa (só Maputo).
- Moatize (distrito) não aparece em nenhuma edição: a tabela só lista "cidades"
  (city proper) submetidas pelo país como tal, e o distrito de Moatize em 1997 era
  majoritariamente rural — não teria sido reportado nessa categoria.
- **Divergência**: nenhuma. Valor idêntico ao registrado em §8 e ao que
  `demograficas.md` já havia recuperado do Wayback (rastreamento pendente lá).
- Licença: UN Terms and Conditions of Use (un.org/en/aboutun/terms) — acesso livre,
  mas uso restrito a "personal, non-commercial use", sem redistribuição nem obras
  derivadas sem autorização escrita. **Nível B**, não A: não atende ao requisito de
  licença que permita "uso, redistribuição e derivadas" do §4.0 do CLAUDE.md.
- **Efeito prático**: o valor de Tete 1997 deixa de depender só de um agregador
  (citypopulation.de/Wikipedia) e passa a ter uma fonte reprocessadora institucional
  citável (UNSD) — mas essa fonte é nível B, então não desbloqueia núcleo A sozinha.
  Serve como confirmação/validação forte do número, não como habilitação de publicação
  em núcleo A.

## 4. IPUMS International — amostras Moçambique 1997/2007/2017 (verificar tabulação agregada pública)
Status: VERIFICADO — permanece nível B, nenhuma tabulação agregada de nível A encontrada.
- URL testada: https://international.ipums.org/international-action/sample_details/country/mz
  → HTTP 200 (2026-09-07).
- Página lista as três amostras de Moçambique como "available": mz1997a (1997, II RGPH),
  mz2007a (2007, III RGPH), mz2017a (2017, IV RGPH). Confirma que IPUMS harmoniza os três
  censos com GEO2_MZ e GEO3_MZ1997/APOSTMZ conforme §4.1 do CLAUDE.md.
- Busca por `sample_details/mz1997a` direta retornou 404; a página funcional é
  `sample_details/country/mz`, que lista as amostras por país (não por amostra individual).
- Não há, nessa página nem nos termos de uso (international.ipums.org/international/terms.shtml,
  já registrado em `demograficas.md`), nenhuma tabulação agregada pública sem cadastro:
  o acesso é só ao microdado, sob termos que proíbem redistribuição.
- **Conclusão**: IPUMS 1997/2007/2017 confirma-se como nível B para os três censos —
  útil apenas para validação (dasimetria, checagem cruzada), nunca como fonte publicável
  de nível A. Não foi baixado nenhum microdado (regra de nível B do CLAUDE.md).

## 5. World Bank Microdata Library / IHSN — ficha do II RGPH 1997
Status: NÃO DISPONÍVEL nesta rodada (não é 404 nem paywall — limitação de scraping).
- URLs testadas: https://microdata.worldbank.org/index.php/catalog/central?q=mozambique+1997+census
  (HTTP 200, mas conteúdo renderizado em cliente via Vue/JS, sem lista de resultados no HTML bruto);
  https://microdata.worldbank.org/index.php/api/catalog?search=Mozambique%20Population%20Census
  (HTTP 200, mas retornou 15 registros genéricos, nenhum de Moçambique — parâmetro `search`
  parece ignorado por esse endpoint); https://microdata.worldbank.org/index.php/api/catalog/central/search?ps=20&sk=mozambique
  (HTTP 400 — parâmetros incorretos para esse endpoint); catalog.ihsn.org (mesmo software
  NADA, mesma limitação, HTTP 200 na página inicial).
- Motivo exato: não foi possível, no tempo desta rodada, identificar o endpoint de API
  correto que o catálogo usa internamente para popular a busca renderizada em
  JavaScript. Isso é uma limitação de método (falta de execução de JS), não uma
  indicação de que o dado não exista ou esteja fechado.
- Registrado como **não disponível nesta rodada** — não como C. Recomenda-se, em
  execução futura, usar um navegador headless ou localizar a documentação da API do
  NADA (geralmente `/index.php/api/catalog/…` com parâmetros diferentes dos testados).

## 6. UNFPA / ReliefWeb / HDX — séries históricas por distrito pré-2017
Status: NÃO DISPONÍVEL nesta rodada — busca incompleta.
- URL testada: https://reliefweb.int/updates?advanced-search=%28PC167%29 → HTTP 202
  (resposta assíncrona típica de app de busca; conteúdo da lista de resultados não foi
  inspecionado em profundidade dentro do tempo desta rodada).
- ReliefWeb é um repositório de relatórios humanitários, não um reprocessador
  estatístico dedicado como CIESIN/UNSD/HDX — mesmo que aceitável pela distinção desta
  tarefa, não seria fonte primária de tabulação censitária, apenas possível ponte para
  documentos de terceiros (que por sua vez precisariam ser rastreados até o INE).
- HDX (item 7/10) já cobre 2017 diretamente com nível A; pré-2017 (1997/2007) não foi
  localizado em ReliefWeb nem em HDX nesta rodada.

## 7. HDX COD-PS Moçambique — vintage 2017 (moz_admpop_adm2_2017_v2.csv)
Status: VERIFICADO — CONFIRMA exatamente Cidade de Tete e Distrito de Moatize 2017.
- URL: https://data.humdata.org/dataset/46b79d47-0667-4baa-8d69-468b208855ed/resource/173abc7f-810a-4022-89dd-c9a9fa40a490/download/moz_admpop_adm2_2017_v2.csv
  → HTTP 200.
- Espelhado em `data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv` (54.556 bytes),
  com `.sha256` e `.meta.json`.
- Linha lida diretamente do CSV: `MZ10,Tete,...,MZ1006,Cidade De Tete,District,...,T_TL=307338`
  e `MZ10,Tete,...,MZ1012,Moatize,District,...,T_TL=260843`.
- **Confirma exatamente** os dois valores de 2017 já recuperados do documento primário
  do INE via Wayback em `demograficas.md` (307.338 e 260.843) — nenhuma divergência.
- Licença: CC BY-IGO 3.0 (creativecommons.org/licenses/by/3.0/igo/legalcode), já
  registrada para o dataset `cod-ps-moz` como nível A em `demograficas.md`. Fonte
  declarada pelo dataset: INE Moçambique, IV RGPH 2017; reprocessador: OCHA
  Mozambique / HDX FIS.
- **Efeito prático**: os valores de 2017 (307.338 e 260.843) agora têm confirmação por
  reprocessador institucional de **nível A**, independente do Wayback/INE. Isso é o
  resultado de maior valor desta rodada depois da prioridade 1 (1997), conforme
  esperado pelo enunciado desta tarefa.

## 8. UNSD Demographic Yearbook — dybcensusdata (tabela interativa) — 2017
Status: NÃO DISPONÍVEL nesta rodada (interface client-side sem endpoint de exportação identificado).
- URL: https://unstats.un.org/unsd/demographic-social/products/dyb/dybcensusdata.cshtml
  → HTTP 200, mas o HTML bruto não contém a tabela de dados (populada via JavaScript).
- Diferente da edição 2007 (item 3), que ainda distribui arquivos .xls estáticos por
  tabela e ano, a versão atual "dybcensusdata" é uma aplicação interativa sem link de
  export .xls/.csv identificável nesta rodada.
- Não crítico: o item 7 (HDX, nível A) já confirma 2017 com os dois valores exatos.

## 9. World Bank Microdata Library / IHSN — ficha do III RGPH 2007 e IV RGPH 2017
Status: NÃO DISPONÍVEL nesta rodada — mesma limitação de scraping do item 5.
- URLs testadas: https://microdata.worldbank.org/index.php/catalog/central?q=mozambique+population+census
  (HTTP 200, sem lista extraível); API com `sk=mozambique` → HTTP 400.
- Não crítico: 2007 tem confirmação parcial pelo item 3 (mesma família UN, mas tabela
  de 1997) e 2017 tem confirmação completa e de nível A pelo item 7.

## 10. HDX COD-PS Moçambique — inventário de vintages (package_show)
Status: VERIFICADO — dataset não cobre 1997 nem 2007.
- URL: https://data.humdata.org/api/3/action/package_show?id=cod-ps-moz → HTTP 200 (API CKAN).
- Campo `resources` lista vintages 2017, 2023, 2024, 2025 (mais antigo: 2017,
  `moz_admpop_2017.xlsx` e CSVs por nível admin). Não há recurso de 1997 nem 2007.
- Licença do dataset: `license_id: cc-by-igo`, `license_url:
  http://creativecommons.org/licenses/by/3.0/igo/legalcode` (mesma do item 7).
- **Conclusão**: HDX COD-PS não é caminho para confirmar 1997; é o caminho de nível A
  já usado no item 7 para confirmar 2017. Vintages 2023–2025 são projeções INE
  pós-censo (não recenseamento), relevantes para §1 pergunta 6/7, fora do escopo
  desta verificação pontual de 1997/2007/2017.

## Veredito

Para cada um dos seis valores-âncora de §8 do CLAUDE.md, o melhor nível de licença
alcançado nesta rodada, via reprocessador institucional (não agregador):

| Âncora | Valor em §8 | Melhor reprocessador encontrado | Nível | Publicável em núcleo A? |
|---|---|---|---|---|
| Cidade de Tete, 1997 | 101.984 | UNSD Demographic Yearbook 2007, Tabela 8 (`data/raw/unsd_dyb2007_table08_capital_cities.xls`) — valor **confirmado, sem divergência** | B | **Não.** UN Terms and Conditions proíbe redistribuição/obras derivadas sem autorização escrita. Só serve como validação/confirmação forte de que o número não é inventado. |
| Distrito de Moatize, 1997 | 109.103 | Nenhum reprocessador institucional localizado nesta rodada (CIESIN/SEDAC inacessível — timeout; World Bank/IHSN não raspável; UNSD Table 8 só lista "cidades", e Moatize não aparece como tal em 1997; IPUMS é B e não expõe tabulação agregada) | não avaliado (não disponível) | **Não.** Permanece sem qualquer reprocessador citável nesta rodada; continua dependendo só do agregador (citypopulation.de) mencionado em §8, o que **não é citável** pela regra §4.0.4. |
| Cidade de Tete, 2007 | 155.870 | Nenhuma segunda via de reprocessador institucional confirmada nesta rodada além do próprio INE (Wayback, já registrado em `demograficas.md`, nível "pendente_auditoria"); UNSD Table 8 2007 só carrega o censo de 1997 para Moçambique, não o de 2007 | não avaliado (não disponível) | **Não muda** — segue no mesmo status de `demograficas.md` (documento primário via Wayback, licença INE não localizável). |
| Distrito de Moatize, 2007 | 215.092 | Idem acima — nenhuma segunda via encontrada | não avaliado (não disponível) | **Não muda.** |
| Cidade de Tete, 2017 | 307.338 (não ajustado) | **HDX COD-PS Moçambique, vintage 2017** (`data/raw/hdx_cod-ps-moz_admpop_adm2_2017_v2.csv`) — valor **confirmado exatamente**, T_TL=307338 | **A** | **Sim.** CC BY-IGO 3.0, reprocessador institucional (OCHA/HDX), origem declarada INE IV RGPH 2017. Converte este valor para núcleo A. |
| Distrito de Moatize, 2017 | 260.843 | **HDX COD-PS Moçambique, vintage 2017** (mesmo arquivo) — valor **confirmado exatamente**, T_TL=260843 | **A** | **Sim**, mesma justificativa acima. |

### A linha de base de 1997 foi recuperada?

**Parcialmente, e só em nível B.** A Cidade de Tete 1997 (101.984) agora tem uma fonte
reprocessadora institucional citável — o UNSD Demographic Yearbook 2007, Tabela 8 —
que confirma o valor exatamente. Isso é estritamente melhor do que depender só de
citypopulation.de/Wikipedia (que nunca poderiam ser citados pela regra §4.0.4), mas a
licença do UNSD (uso pessoal não-comercial, sem redistribuição nem obras derivadas sem
autorização escrita) é **nível B**, não A. Portanto **o valor pode ser citado no texto
com a ressalva de nível B e fonte UNSD**, mas **não pode sustentar um número em tabela
de resultados do núcleo reprodutível** (regra §4.0, "apenas fontes de nível A
sustentam números publicados").

O Distrito de Moatize 1997 (109.103) **não foi recuperado** por nenhum reprocessador
institucional nesta rodada: CIESIN/SEDAC (a pista mais forte apontada no enunciado)
esteve inacessível (timeout, `curl -m 20` retornando `000`/exit 28 em múltiplas
tentativas) durante toda a janela desta execução — não é um "não existe", é uma falha
de acesso ao servidor que deveria ser reexecutada. A tabela do UNSD que confirmou Tete
só lista "cidades" (city proper) submetidas pelo país, e Moatize em 1997 era um
distrito majoritariamente rural, não elegível a essa categoria.

**Conclusão para `docs/ADR/0003`:** como nenhum dos dois valores de 1997 chegou a
nível A (Tete ficou em B; Moatize permanece sem reprocessador), **o ADR não precisa
ser revisto por esta rodada** — a linha de base por área construída continua sendo a
melhor alternativa disponível para 1997 no núcleo reprodutível A. Se uma execução
futura conseguir acessar CIESIN/SEDAC (hoje inacessível) e ele expuser tabulações de
Moçambique por distrito em nível CC-BY-4.0 (nível A) cobrindo Moatize 1997, **então
sim** o ADR 0003 precisaria ser reaberto — mas isso não aconteceu nesta rodada.

O maior ganho concreto desta rodada é a **elevação de 2017 (ambos os valores) para
núcleo A** via HDX COD-PS, que antes dependia só do documento do INE via Wayback sem
licença localizável ("pendente_auditoria" em `demograficas.md`). Isso desbloqueia
diretamente o pilar demográfico de §5.3 para o ano de 2017, o mais recente censo.

---

## Acréscimo do orquestrador — COD-PS vintages 2024/2025 (2026-09-07)

A rodada anterior consultou o COD-PS apenas no vintage 2017. Consultando a API do CKAN do
HDX (`package_show?id=cod-ps-moz`), o mesmo dataset publica também os vintages **2023, 2024
e 2025**, com notas técnicas próprias.

Espelhado: `data/raw/hdx_cod-ps-moz_admpop_adm2_2025.csv` (com `.sha256` e `.meta.json`).

| Unidade | P-code | Homens | Mulheres | Total 2025 |
|---|---|---|---|---|
| Cidade De Tete | MZ1006 | 229.296 | 230.952 | **460.248** |
| Moatize | MZ1012 | 171.221 | 177.882 | **349.103** |

**Licença CC BY-IGO 3.0 → nível A.** Origem declarada: projeções do INE.

**Selo obrigatório: `modelado`.** São projeções, não contagem censitária, e não podem ser
apresentadas como população recenseada. §5.3 exige o selo explícito.

### Por que isto importa

`data/DATA_AUDIT.md` concluiu que a **pergunta 6 de §1** (bust e transição, 2015–2025) era
irrespondível por não haver âncora demográfica depois de 2017. Com o COD-PS, passa a haver
uma ponta em 2025 de nível A — modelada, mas citável. A pergunta muda de "não respondível"
para "respondível com ressalva de selo".

Não resolve 1997 nem 2007, que continuam sem fonte de nível A.

### Via esgotada nesta rodada

**CIESIN/SEDAC está fora do ar** — `sedac.ciesin.columbia.edu` devolve **000** em todas as
tentativas, igual a `ine.gov.mz`. Era a via mais promissora para 1997 e 2007 por distrito,
porque o GPW publica os dados de entrada por unidade administrativa. Não foi falha de busca:
o servidor não responde. **Retomar quando voltar.**
