# PROVENANCE — Fontes Demográficas e Domiciliares

Tentativa 4. Rastreabilidade de arquivos efetivamente baixados para `data/raw/`.
Última atualização: 2026-09-07 (esqueleto).

## Arquivos baixados

| # | Arquivo local | URL (snapshot/original) | Data de acesso | Licença | Nível | Resolução/nível geográfico | Anos cobertos | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | data/raw/censo2007-tete-quadro3-populacao-por-idade-distrito-2007.html | https://web.archive.org/web/20100809032728id_/http://www.ine.gov.mz/censo2007/rdcenso09/Tete/c0705q3 | 2026-09-07 | pendente_auditoria (INE, primário via Wayback; sem texto de licença localizado) | pendente_auditoria | distrito/cidade, Província de Tete | 2007 | OK |
| 2 | data/raw/quadro-3-populacao-por-idade-segundo-area-de-residencia-distrito-e-sexo-provincia-de-tete-2017.xlsx | https://web.archive.org/web/20191114015524id_/http://www.ine.gov.mz/iv-rgph-2017/tete/quadro-3-populacao-por-idade-segundo-area-de-residencia-distrito-e-sexo-provincia-de-tete-2017.xlsx | 2026-09-07 | pendente_auditoria (INE, primário via Wayback; sem texto de licença localizado) | pendente_auditoria | distrito/cidade, Província de Tete | 2017 | OK |
| 3 | data/raw/censo-2017-brochura-dos-resultados-definitivos-do-iv-rgph-nacional.pdf | https://web.archive.org/web/20190501151428id_/http://www.ine.gov.mz/iv-rgph-2017/mocambique/censo-2017-brochura-dos-resultados-definitivos-do-iv-rgph-nacional.pdf | 2026-09-07 | pendente_auditoria (INE, primário via Wayback; sem texto de licença localizado) | pendente_auditoria | nacional/provincial | 2017 | OK |
| 4 | data/raw/hdx_cod-ab-moz_admin_boundaries.xlsx | https://data.humdata.org/dataset/5e8d83a5-1210-49be-b7d9-cf286dbc15df/resource/47ea3adb-8370-4aba-9f0f-bed6087199de/download/moz_admin_boundaries.xlsx | 2026-09-07 | CC BY-IGO (https://creativecommons.org/licenses/by/3.0/igo/legalcode) | A | admin0-4 (país/província/distrito/posto/localidade) | limites válidos a partir de 2017-01-01 (dataset v02, revisado 2026-03-10) | OK |

## Âncoras de §8 — verificação contra fonte primária

| Unidade | Ano | Valor em §8 | Valor lido em fonte primária | URL do snapshot | Quadro/página | Veredito |
|---|---|---|---|---|---|---|
| Cidade de Tete | 1997 | 101.984 | não disponível | — | — | NÃO LOCALIZADO EM FONTE PRIMÁRIA |
| Cidade de Tete | 2007 | 155.870 | 155.870 | https://web.archive.org/web/20100809032728id_/http://www.ine.gov.mz/censo2007/rdcenso09/Tete/c0705q3 | Quadro 3 (III RGPH 2007, Tete) | CONFIRMADO |
| Cidade de Tete | 2017 | 305.722 ou 307.338 | 307.338 (305.722 não consta deste quadro) | https://web.archive.org/web/20191114015524id_/http://www.ine.gov.mz/iv-rgph-2017/tete/quadro-3-... .xlsx | Quadro 3 (IV RGPH 2017, Tete) | DIVERGENTE PARCIAL — 307.338 confirmado; 305.722 não localizado em fonte primária |
| Distrito de Moatize | 1997 | 109.103 | não disponível | — | — | NÃO LOCALIZADO EM FONTE PRIMÁRIA |
| Distrito de Moatize | 2007 | 215.092 | 215.092 | https://web.archive.org/web/20100809032728id_/http://www.ine.gov.mz/censo2007/rdcenso09/Tete/c0705q3 | Quadro 3 (III RGPH 2007, Tete) | CONFIRMADO |
| Distrito de Moatize | 2017 | 260.843 | 260.843 (grafia da fonte: "MAOATIZE") | https://web.archive.org/web/20191114015524id_/http://www.ine.gov.mz/iv-rgph-2017/tete/quadro-3-... .xlsx | Quadro 3 (IV RGPH 2017, Tete) | CONFIRMADO |

## Questões a resolver (§ orquestrador)

- **(a) A que recorte correspondem 305.722 e 307.338.** 307.338 é o valor lido diretamente
  no Quadro 3 do IV RGPH 2017 (Tete), linha "CIDADE DE TETE", coluna TOTAL — **confirmado em
  fonte primária** (`data/raw/quadro-3-...-2017.xlsx`). **305.722 não aparece em nenhum lugar
  do Quadro 3 nem na brochura nacional** (`data/raw/censo-2017-brochura-...-nacional.pdf`,
  varrida por busca textual por "305 722"/"305722": zero ocorrências). Hipóteses não
  verificadas para a origem de 305.722: (i) população "presente" ou "residente" com outro
  ajuste censitário não publicado nos quadros consultados; (ii) erro de transcrição em
  agregador (citypopulation.de/Wikipedia); (iii) recorte de limite administrativo diferente
  (ex.: cidade sem um bairro periférico). Sem documento primário que o contenha, **305.722
  fica como "não disponível / não confirmado"** — não deve ser citado no núcleo do estudo.

- **(b) Sub-enumeração de 3,7% — documentada e incorporada?** Documentada: **sim**, na
  brochura nacional do IV RGPH 2017, página do "QUADRO DO TAMANHO DA POPULAÇÃO DE
  MOÇAMBIQUE, 2017" (`data/raw/censo-2017-brochura-...-nacional.pdf`). O quadro apresenta,
  por província, três colunas: "População Total (Ajustada à Taxa de Omissão)", "Taxa de
  Omissão" e "População Residente a 1 de Agosto de 2017". Para Moçambique: população
  ajustada = 27.909.798; taxa de omissão = **3,7%**; população residente (não ajustada) =
  26.899.105. Para a província de Tete especificamente a taxa foi 3,8% (mulheres 3,7%),
  população ajustada 2.648.941 vs. residente 2.551.826.
  **Incorporada nos números distritais/municipais publicados nos quadros provinciais?
  NÃO.** Verificação direta: o TOTAL da linha "T O T A L" do Quadro 3 da província de Tete
  (2017) é **2.551.826** — exatamente igual à "População Residente" (não ajustada) do
  quadro nacional, e não aos 2.648.941 ajustados. Logo, **307.338 (Cidade de Tete) e 260.843
  (Distrito de Moatize) são contagens residentes, sem o ajuste de omissão — 3,8% na Província de Tete
  (a taxa pertinente a estas unidades) e 3,7% no total nacional: duas taxas de
  unidades diferentes, NÃO uma faixa de incerteza de uma só grandeza
  aplicado.** Isso é relevante para H1 e para qualquer comparação com o total oficial do
  país: os números distritais publicados sistematicamente subestimam a população "real"
  estimada pelo INE em cerca de 3-6% a mais, dependendo da província.

- **(c) Mudança de limites do Distrito de Moatize entre censos.** Não foi possível
  confirmar ou refutar diretamente com documento cartográfico de 1997/2007/2017 dentro do
  tempo disponível nesta rodada. Indício indireto: o COD-AB (HDX, `data/raw/hdx_cod-ab-moz_admin_boundaries.xlsx`,
  metodologia declarada no próprio dataset) afirma explicitamente que os limites ADM3/ADM4
  atuais foram objeto de "ajustes não oficiais" pela OCHA/PMA para corrigir desalinhamentos
  com os censos de 2017, e que uma atualização oficial de limites administrativos só é
  esperada em 2027 — ou seja, o próprio INE reconhece que a malha administrativa vigente
  ainda deriva da base de 2017 sem revisão completa. Isso não prova mudança 1997→2007→2017,
  mas mostra que a malha não é estática e que qualquer comparação direta de área/população
  por "Distrito de Moatize" ao longo do tempo **precisa de nota metodológica explícita de
  não comparabilidade garantida**, até que se localizem os mapas/codificadores de cada
  censo (não localizados nesta rodada). Registrar como **não resolvido — requer fonte
  cartográfica dedicada (INE/DINAGECA/ANTG), fora do escopo desta verificação textual**.

## Censo 1997 (II RGPH) — busca dedicada
Status: CONCLUÍDA — não disponível em fonte primária acessível.

Buscas feitas (todas via CDX do Wayback Machine, `web.archive.org/cdx/search/cdx`, 2026-09-07):
1. `ine.gov.mz/censo97/*` (filtro statuscode:200, colapsado por urlkey, limite 500) — 123 capturas.
   Estrutura: pastas numéricas `00`–`11` = brochuras provinciais "II RECENSEAMENTO GERAL DA
   POPULAÇÃO E HABITAÇÃO 1997 — INDICADORES SÓCIO-DEMOGRÁFICOS" por província (confirmado por
   inspeção de `<n>introdu.htm` em cada pasta): 00=País, 01=Niassa, 02=Cabo Delgado,
   04=Zambézia, 05=**Tete**, 08=Inhambane, 09=Gaza, 10=Maputo (Cidade/Província). Não há pasta
   por distrito ou cidade.
2. Pasta `05` (Tete) tem só 8 arquivos arquivados: `05estado.htm`, `05forcade.htm`,
   `05fucundidade.htm`, `05habitaca.htm`, `05introdu.htm`, `05linguas.htm`, `brochura.htm`,
   `imagens/t_05indicadores.gif`. O índice `brochura.htm` (arquivado em
   `https://web.archive.org/web/20000124214016id_/http://www.ine.gov.mz:80/Censo97/05/brochura/brochura.htm`)
   lista 14 seções, incluindo `05dados.htm` (DADOS BÁSICOS) e `05populacao.htm` (TAMANHO,
   ESTRUTURA E CRESCIMENTO DA POPULAÇÃO) — exatamente as páginas que conteriam os números de
   população — mas **nenhuma das duas foi rastreada pelo crawler do Internet Archive em
   nenhuma data** (consulta CDX específica para essas duas URLs: zero capturas, qualquer
   status). `05mortalidade.htm` e `05agregado.htm` foram rastreados mas retornaram 404 já em
   2000-07-08 (arquivo removido do servidor antes de ser espelhado).
3. Mesmo se recuperadas, as brochuras do II RGPH 1997 são de nível **provincial**, não
   distrital/municipal — não há evidência de que contivessem tabela "Cidade de Tete" ou
   "Distrito de Moatize" (o `id_tete` de 2007 mostra que essas brochuras trazem apenas
   indicadores da província inteira, comparando 1997 vs 2007 a esse nível).
4. `ine.gov.mz/censos_dir/*` — existe, mas cobre exclusivamente Censo Agro-Pecuário e Censo
   às Empresas (CEMPRE); nenhum arquivo relativo ao II RGPH 1997 população.
5. `ine.gov.mz/ii-rgph*` e `ine.gov.mz/IIRGPH*` — zero capturas.
6. `ine.gov.mz/censo1997/*` — não testado isoladamente (redundante com `censo97/*`, que já
   cobre o padrão real de URL usado pelo INE).
7. mozdata.ine.gov.mz — confirmado por execução anterior que não lista o Censo 1997 (II RGPH)
   em seu catálogo.

**Conclusão:** os valores de §8 para 1997 (Cidade de Tete = 101.984; Distrito de Moatize =
109.103) **não puderam ser confirmados em fonte primária**. Não há documento do INE
acessível (nem ao vivo, nem arquivado) com desagregação distrital/municipal do II RGPH 1997
para a província de Tete. Motivo exato: páginas candidatas (`05dados.htm`, `05populacao.htm`)
nunca foram rastreadas pelo Internet Archive antes de saírem do ar; o site atual
(`ine.gov.mz`) está fora do ar (000) desde a verificação de 2026-09-07. Os valores de §8
permanecem como citação de agregador (citypopulation.de/Wikipedia) e **não devem ser usados
como número publicado** — apenas como hipótese de trabalho para a linha de base contrafactual
de H1, com selo "não verificado em fonte primária".

## Suficiência para §1

**Pergunta 1 (linha de base 1997–2005) e H1 (aceleração de ~4%/ano para ~7%/ano):**
**parcialmente respondível, com lacuna séria na ponta 1997.** Os anos-âncora 2007 e 2017
estão confirmados em fonte primária (Cidade de Tete: 155.870 em 2007, 307.338 em 2017;
Distrito de Moatize: 215.092 em 2007, 260.843 em 2017 — todos não ajustados pela taxa de
omissão de 3,8% da Província de Tete; a nacional, 3,7%, é outra grandeza). O ano-âncora 1997 **não foi confirmado em fonte primária** (busca
exaustiva no Wayback, ver seção acima) — os valores de §8 (101.984 e 109.103) continuam
como citação de agregador, não verificável. Isso significa que a CAGR pré-2005 (ponta do
H1) só pode ser calculada com um número não verificado, o que deve ser declarado
explicitamente no artigo/app como "não observado / fonte não localizada" caso não se
encontre alternativa (ex.: publicação impressa do INE digitalizada por terceiros, ou
consulta direta ao INE). A CAGR 2007→2017 (a segunda perna de H1) é computável e sólida.

**Pergunta 6 (bust e transição, 2015–2025):** os dados desta família **não cobrem** esse
período — o próximo censo é 2027 (ainda não realizado/publicado). Séries demográficas para
2015–2025 dependem de projeções do INE (não localizadas nesta busca) ou de proxies de outras
famílias (imagem, luzes noturnas), fora do escopo desta verificação. **Não respondível com
esta família isoladamente.**

**H1 especificamente:** testável apenas com ressalva. Recomenda-se: (i) manter 1997 como
"não verificado" e não usá-lo em nenhum número publicado no núcleo A; (ii) se o
`auditor-dados` aceitar 1997 como validação B (citação de agregador, rotulada como tal), a
hipótese pode ser explorada em caráter exploratório, nunca como conclusão do núcleo A;
(iii) qualquer comparação de área/população do "Distrito de Moatize" ao longo do tempo deve
vir acompanhada da ressalva de (c) sobre possível mudança de limites administrativos, ainda
não resolvida.

**O que falta, especificamente:**
1. Um documento primário do INE com Cidade de Tete/Distrito de Moatize para 1997 (não
   localizado no Wayback; pode existir em acervo físico do INE ou publicação impressa não
   digitalizada).
2. Confirmação cartográfica de mudança de limites do Distrito de Moatize 1997→2007→2017
   (fora do escopo desta busca textual).
3. Origem do número 305.722 (não localizado em nenhum documento primário consultado).

---

## RECONCILIAÇÃO — 2026-09-08

A avaliação acima trata **H1 na formulação original, em população** ("aceleração de ~4 %/ano
para ~7 %/ano"), e a classifica como "parcialmente respondível, com lacuna séria na ponta
1997". Duas decisões posteriores mudam isso:

- **`docs/ADR/0003`** reformulou H1 em termos de **área construída**, não de habitantes,
  precisamente porque o Censo de 1997 não existe em fonte acessível. A formulação em
  população **não é mais a hipótese do estudo**.
- **A emenda de 2026-09-08 ao `docs/ADR/0008`** restringe ainda mais a formulação em área:
  ela vale sobre **taxa de primeira detecção**, não sobre estoque, porque nem a classificação
  própria (regra R2) nem o WSF Evolution (formato do dado) fornecem estoque sem
  monotonicidade imposta.

O conteúdo factual deste fragmento — licenças, âncoras verificadas, o que existe e o que não
existe — **permanece válido**. O que caducou é a avaliação de testabilidade de H1, que foi
feita antes das reformulações.
