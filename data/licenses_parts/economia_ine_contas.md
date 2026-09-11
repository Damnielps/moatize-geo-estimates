# LICENSES — Contas Regionais / PIB provincial do INE (§4.4/§4.0 CLAUDE.md)

Fase 4b, tarefa A2c (camada T2). Última atualização: 2026-09-11 (retentativa com shell).
Rodada original (WebFetch): nenhum número localizado. Retentativa com `curl`/Wayback
(seção "Retentativa com shell" abaixo): um documento primário (Folheto Provincial Tete
2021) foi lido e um número de PIB provincial de contexto foi publicado em
`data/processed/economia/contas_regionais_tete.csv` — ver
`data/provenance_parts/economia_ine_contas.md`. O ficheiro
`contas_regionais_tete.AUSENTE.md` foi removido nesta retentativa por deixar de
refletir o estado atual; este fragmento registra o estado de acesso/licença, que
permanece **C**.

| Fonte | URL canônica | Licença (texto/link) | Nível | Restrições | Citação exigida | Verificado em |
|---|---|---|---|---|---|---|
| INE — publicações econômicas provinciais ("Indicadores em Flash", "Folheto Estatístico Provincial", possível "Contas Regionais") | https://ine.gov.mz/estatisticas/estatisticas-economicas ; https://ine.gov.mz/documents/20119/... (PDFs por província) | não localizado — todas as tentativas de acesso ao domínio `ine.gov.mz`/`www.ine.gov.mz` falharam por erro de certificado TLS (`unable to verify the first certificate`) nesta rodada; conteúdo e página de termos **não lidos** | C (precedente §4.0.1: sem licença localizável ⇒ C; aqui o próprio conteúdo é inacessível, condição ainda mais restritiva que o precedente de 2007/2017, em que ao menos o conteúdo primário foi lido via Wayback) | Acesso ao domínio vivo instável (mesmo padrão já registrado em `data/licenses_parts/demograficas.md` para 2026-09-07); conteúdo numérico não confirmado | INE Moçambique (citação institucional padrão, a confirmar se o documento for lido) | 2026-09-11 |
| Wayback Machine — snapshots de `ine.gov.mz` para as mesmas publicações | web.archive.org | não avaliado — a ferramenta de acesso desta sessão (`WebFetch`) recusou explicitamente requisições a `web.archive.org` ("unable to fetch from web.archive.org"); diferente da família demográfica, aqui não há confirmação de existência ou ausência de snapshot | pendente_auditoria (bloqueio de ferramenta, não de dado — outro agente/sessão com acesso a `web.archive.org` deve repetir a tentativa) | — | — | 2026-09-11 |
| mozdata.ine.gov.mz | https://mozdata.ine.gov.mz | não avaliado — página respondeu mas sem conteúdo estruturado extraível nesta rodada (mesma limitação já registrada em `data/licenses_parts/demograficas.md`) | pendente_auditoria | — | — | 2026-09-11 |
| Banco Mundial — World Bank Open Data (indicadores de PIB) | https://data.worldbank.org/country/MZ | CC BY 4.0 (licença padrão do World Bank Open Data) — **mas não existe, nos indicadores consultados, produto de PIB subnacional/provincial para Moçambique**; produto inexistente, não uma questão de licença | não aplicável — dado não existe nesta fonte | — | — | 2026-09-11 |
| UNU-WIDER — Mozambique Data Hub | https://www.wider.unu.edu/database/mozambique-data-hub | não verificado nesta rodada — hub existe, licença e conteúdo item a item não inspecionados; não confirmado se contém série de PIB/VAB provincial de Tete | pendente_auditoria | — | — | 2026-09-11 |
| Banco de Moçambique — Estatísticas de PIB | https://www.bancomoc.mz/pt/areas-de-actuacao/estatisticas/dominios-e-indicadores-estatisticos/produto-interno-bruto/ | não verificado nesta rodada; títulos localizados indicam PIB **nacional**, sem indicação de desagregação provincial | não aplicável (nível não avaliado; produto parece ser nacional, não provincial) | — | — | 2026-09-11 |

## Notas

- Este fragmento **não altera** o precedente C já registrado para os documentos de
  Censo 2007/2017 do INE em `data/licenses_parts/demograficas.md`. Aqui a situação é
  distinta e mais restritiva: nem o conteúdo primário pôde ser lido (erro de
  certificado TLS em toda tentativa contra `ine.gov.mz`), então não há nem sequer a
  base factual que naquele precedente permitiu "pendente_auditoria". Classificação
  proposta para esta família: **C** por regra §4.0.1 (sem licença localizável — e,
  aqui, sem conteúdo localizável) até nova tentativa de acesso.
- Nenhum reprocessador de nível A com os números de PIB/VAB provincial de Tete foi
  confirmado nesta rodada (World Bank não tem o produto; UNU-WIDER não inspecionado
  a fundo; Banco de Moçambique parece cobrir só o nível nacional).

## Retentativa com shell (2026-09-11)

Com acesso a `curl` (fora da sessão anterior, limitada a `WebFetch`), foi possível
consultar a API CDX do Wayback Machine (`web.archive.org/cdx/search/cdx`) para o
domínio `ine.gov.mz` filtrando por `tete`, `pib` e `contas`. Dois documentos primários
foram lidos com sucesso via snapshot (`.../web/<timestamp>id_/<url>`, que devolve o
bruto com TLS válido do próprio archive.org):

1. `http://www.ine.gov.mz/censo2007/rdcenso09/Tete/indicadores_macro_economicos/cn/pib`
   (snapshot 20100811204457) — página de navegação do Censo 2007 sob a árvore "Tete",
   mas os links de "Contas Nacionais Anuais" apontam para
   `http://www.ine.gov.mz/indicadores_macro_economicos/cn/pib/...` — **sem** o segmento
   `/Tete/`. Confirma que esta seção é um template nacional replicado por província no
   breadcrumb, não uma série de PIB provincial. **Nenhum número lido desta página.**
   Não altera a classificação C (agora: produto de PIB provincial por ramo de atividade
   continua não localizado, e esta página mostra explicitamente por que não existe).
2. `https://ine.gov.mz/documents/20119/176900/Folheto%20Provincial_Tete_2021.pdf`
   (snapshot Wayback 20251116031649, `application/pdf`, 530.924 bytes) — **este sim
   contém números**: quadro "PIB e Inflação" com taxa de crescimento do PIB real (2020),
   PIB per capita em US$ (2020), PIB da província em % do PIB nacional (2020), inflação
   média e acumulada (2021), Província × Nacional. **Não é uma série de Contas Regionais
   por ramo de atividade** (o pedido original de A2c) — é um único ano de indicadores
   agregados, sem desagregação setorial. Espelhado em
   `data/raw/ine_contas_folheto_provincial_tete_2021.pdf` com `.sha256` e `.meta.json`.
   Licença: **não localizada** no PDF nem no domínio (a URL canônica `ine.gov.mz`
   permanece inacessível por erro de certificado TLS nesta sessão) ⇒ **nível C**,
   inalterado — apenas o conteúdo, que antes era totalmente desconhecido, passa a ser
   lido e registrado como contexto. Ver `data/processed/economia/contas_regionais_tete.csv`.
