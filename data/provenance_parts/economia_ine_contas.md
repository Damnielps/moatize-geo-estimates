# PROVENANCE — Contas Regionais / PIB provincial do INE (Tete)

Fase 4b, tarefa A2c (camada T2). Última atualização: 2026-09-11 (retentativa com shell).

## Arquivos baixados (rodada original, WebFetch)

Nenhum. Nenhum documento foi lido com sucesso — todas as tentativas de acesso a
`ine.gov.mz`/`www.ine.gov.mz` retornaram erro de certificado TLS
(`unable to verify the first certificate`); todas as tentativas de acesso a
`web.archive.org` foram recusadas pela ferramenta desta sessão. `mozdata.ine.gov.mz`
respondeu, mas sem conteúdo estruturado extraível. **Na retentativa com shell
(seção abaixo) um documento foi lido com sucesso via Wayback Machine** — ver
`data/raw/ine_contas_folheto_provincial_tete_2021.pdf`. O ficheiro
`contas_regionais_tete.AUSENTE.md`, referido abaixo, foi removido por deixar de
refletir o estado atual.

| # | Arquivo local | URL tentada | Data de acesso | Resultado |
|---|---|---|---|---|
| — | (nenhum) | https://ine.gov.mz/documents/20119/251951/Indicadores%20em%20flash_Provincia_Tete_2023.pdf/... | 2026-09-11 | FALHA — erro de certificado TLS |
| — | (nenhum) | https://ine.gov.mz/documents/20119/322405/Folheto_Estatistico_Provincia_Tete_2025.pdf/... | 2026-09-11 | FALHA — erro de certificado TLS |
| — | (nenhum) | https://www.ine.gov.mz/documents/20119/260564/Folheto%20Distrital%20Moatize%202023.pdf/... | 2026-09-11 | FALHA — erro de certificado TLS |
| — | (nenhum) | http://www.ine.gov.mz/estatisticas/estatisticas-economicas | 2026-09-11 | FALHA — erro de certificado TLS |
| — | (nenhum) | https://mozdata.ine.gov.mz | 2026-09-11 | acessível, sem conteúdo estruturado extraído |
| — | (nenhum) | web.archive.org (snapshot dos PDFs acima; CDX API) | 2026-09-11 | FALHA — ferramenta recusou o domínio |

## Suficiência para §1

Nenhuma pergunta específica de §1 depende exclusivamente de PIB/VAB provincial: a
"base econômica" e os "proxies econômicos" do estudo (P5, P6, H3, H4) são cobertos,
no núcleo de nível A, por luzes noturnas (Chen/Yu 2021), classificação orbital
(área industrial/construída) e relatórios de produção declarados pelos operadores
(`data/processed/economia/producao_moatize_anual.csv`), não por Contas Regionais.
Esta família seria **contexto complementar** (magnitude monetária do PIB provincial
e sua composição setorial), não uma via alternativa às perguntas já respondidas por
outras famílias. Sua ausência não rebaixa nenhum veredito já registrado em
`data/DATA_AUDIT.md` para P5/P6/H3/H4 — apenas significa que o app/artigo não podem
apresentar "PIB da Província de Tete em MZN" como número publicado.

## O que falta, especificamente (rodada original)
Uma série de Contas Regionais / PIB por ramo de atividade para a província ainda
não foi localizada (ver seção "Retentativa com shell" abaixo). Um único ano de
indicadores macroeconômicos agregados foi lido e publicado como contexto.

## Retentativa com shell (2026-09-11)

Nova rodada, com `curl` disponível (agente com shell). Consulta à API CDX do Wayback
Machine (`web.archive.org/cdx/search/cdx?url=ine.gov.mz*&filter=urlkey:.*tete.*`)
localizou dois documentos primários acessíveis via snapshot (`.../web/<timestamp>id_/`):

| # | Arquivo local | URL original | Data de acesso | Data de captura (snapshot) | Resultado |
|---|---|---|---|---|---|
| 1 | (nenhum — página de navegação, sem número) | `http://www.ine.gov.mz/censo2007/rdcenso09/Tete/indicadores_macro_economicos/cn/pib` | 2026-09-11 | 2010-08-11 | LIDA — confirma que a seção "Contas Nacionais" sob a árvore Tete é template nacional (links sem `/Tete/`); nenhum PIB provincial nesta página |
| 2 | `data/raw/ine_contas_folheto_provincial_tete_2021.pdf` | `https://ine.gov.mz/documents/20119/176900/Folheto%20Provincial_Tete_2021.pdf` | 2026-09-11 | 2025-11-16 | LIDA — quadro "PIB e Inflação" (2020/2021), Província de Tete × Nacional |

Licença do item 2: não localizada (nem no PDF, nem no domínio `ine.gov.mz`, inacessível
por TLS nesta sessão) ⇒ nível **C**. Citação: INE — Folheto Provincial, Província de
Tete, 2021 (fonte declarada no documento: INE, Direcção de Contas Nacionais,
Indicadores Globais).

Números publicados em `data/processed/economia/contas_regionais_tete.csv`: taxa de
crescimento do PIB real (2020), PIB per capita em US$ (2020), PIB provincial em % do
PIB nacional (2020), inflação média e acumulada (2021) — Província de Tete e
Moçambique. **Não é uma série de Contas Regionais por ramo de atividade**: é um único
ano de indicadores macroeconômicos agregados, publicado num folheto de indicadores
socioeconômicos gerais, não numa publicação dedicada de "Contas Regionais". A busca por
uma série anual de PIB/VAB por ramo de atividade para a província permanece sem
resultado — o item 1 desta tabela mostra que a estrutura "Contas Nacionais" do site do
INE é nacional, não provincial, o que é evidência de que tal série pode não existir
como produto do INE.

Todas as demais tentativas registradas na rodada anterior (WebFetch) permanecem como
estavam: nenhum reprocessador de nível A ou B foi confirmado (World Bank sem produto
subnacional; UNU-WIDER não inspecionado a fundo; Banco de Moçambique só nacional).

### Suficiência para §1 (atualização)

Inalterada: nenhuma pergunta de §1 depende exclusivamente de Contas Regionais. O único
número agora disponível (PIB provincial em % do PIB nacional, 2020) é publicável apenas
como **contexto de nível C**, nunca como número do núcleo A — consistente com o
veredito já registrado.

## Regeneração por script (2026-09-11, reexecução T3 após reprovação no portão)

O CSV `data/processed/economia/contas_regionais_tete.csv` deixou de ser transcrição
manual: é gerado por `pipeline/00_fetch/extrair_ine_folheto_tete.py` (§11.2), chamado
no alvo `fetch` do Makefile (explicitamente, fora do laço `|| true`, para que falhas
sejam fatais).

- **Bruto:** `data/raw/ine_contas_folheto_provincial_tete_2021.pdf`, sha256
  `ca05e1fb7d6927256daeeceae302603c5b725e435b337025cb9e53855794bfe5`. Se ausente, o
  script baixa da URL Wayback `id_` do `.meta.json` e confere o hash; divergência ⇒
  falha, nada gravado.
- **Extração:** texto via `pypdf`; quadro localizado pelo cabeçalho "PIB e Inflação
  Provincia Nacional" e pela linha "Fonte: INE, Direcção de Contas Nacionais,
  Indicadores Globais"; cada um dos 5 rótulos de linha (2 colunas: Província, Nacional)
  tem de casar exatamente uma vez, senão o script falha. O ano de cada linha é lido do
  próprio rótulo. Verificação interna: coluna Nacional de "PIB em % do PIB Nacional" = 100,0.
- **Saída:** 9 linhas, mesmas colunas, valores, `fonte`, `nota` e ordem da transcrição
  anterior; única diferença é a coluna `metodo`, que passou de "transcrição direta do
  quadro do folheto provincial" para "extraído por pipeline/00_fetch/extrair_ine_folheto_tete.py
  do texto do PDF (pypdf), quadro 'PIB e Inflação'". sha256 do CSV:
  antes `b57974d255591993b55b653cad4cfcb9b7fa336bad7fb4f23542a85743ab9ccc` (manual),
  depois `a51e8f608fdcc3539d8ffa8abc9cbd6f85e15b689433e97ee39d7d7d43749440` (script).
  Substituir o texto de `metodo` no arquivo anterior produz exatamente os bytes novos.
- **Contrato:** `pipeline/tests/test_economia.py` (`test_contas_ine_*`), incluindo
  regeneração byte a byte (pula se o PDF bruto não estiver no cache local).
- Nível permanece **C**: contexto, não núcleo (§4.0).
