<!-- SECAO_ECONOMIA_PRODUCAO_INICIO -->
## Produção de carvão — Vale 20-F / Vulcan / GEM Coal Tracker (Fase 4b, T A2b)

| Fonte | URL canônica | Licença | Nível provisório | Restrições | Citação exigida | Data de verificação |
|---|---|---|---|---|---|---|
| SEC EDGAR — Vale S.A. Form 20-F (CIK 0000917851) | https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000917851&type=20-F ; API: https://data.sec.gov/submissions/CIK0000917851.json | "Website Dissemination" — https://www.sec.gov/about/privacy-information: "Information presented on sec.gov is considered public information and may be copied or further distributed by users of the web site without the SEC's permission. Please consider appropriate citation to the SEC as the source." | A | Não usar o selo/logo da SEC ou EDGAR como marca; citar a SEC como fonte. A SEC exige, além disso, que todo acesso automatizado identifique um contato real no cabeçalho `User-Agent`, no formato "Nome Sobrenome email@dominio" (https://www.sec.gov/os/webmaster-faq#developers) — **restrição operacional corrigida em 2026-09-11 (reexecução T2): o 403 registrado em execução anterior desta linha era causado por um literal de contato inválido (`...@users.noreply.github.com`), não por um bloqueio geral da SEC; ver correção completa em `data/provenance_parts/economia_producao.md` e docstring de `pipeline/00_fetch/fetch_vale_20f.py`.** | Vale S.A., Form 20-F [ano], SEC EDGAR, CIK 0000917851 | 2026-09-11 |
| Vulcan International (Vulcan Mozambique) — página oficial "Performance" | https://www.vulcaninternational.com/performance/ | Página sob aviso de "Disclaimer" (https://www.vulcaninternational.com/disclaimer/): "The copyright for any material created by the author is reserved. Any duplication or use of objects such as images, diagrams, sounds or texts in other electronic or printed publications is not permitted without the author's agreement." Nenhuma licença aberta localizada. | C (excluída) | Todos os direitos reservados; sem licença de reuso localizável → nível C por §4.0 regra 1. | Não aplicável (fonte excluída; não citar como número na tabela de resultados) | 2026-09-11 |
| Global Energy Monitor — Global Coal Mine Tracker (dataset) | https://globalenergymonitor.org/projects/global-coal-mine-tracker/#download | Download via formulário (widget `gem-download-form`, slug `coal-mine-tracker`) exigindo nome/e-mail — não preenchido, por instrução da tarefa (não fornecer dados pessoais). | B | Cadastro obrigatório para acesso ao dataset bruto; não redistribuível; não sustenta número publicado (§4.0). | Global Energy Monitor, "Global Coal Mine Tracker", [data de acesso] | 2026-09-11 |
| GEM Wiki — páginas descritivas das minas (ex. Moatize mine, Benga coal mine, Chirodzi coal mine) | https://www.gem.wiki/Moatize_mine | Creative Commons Attribution-NonCommercial-ShareAlike 4.0 (verificado no rodapé da página: `<link rel="license" href="https://creativecommons.org/licenses/by-nc-sa/4.0/">`) | B | Cláusula NonCommercial — restringe uso comercial; §4.0 classifica como B ("restringe a uso não comercial"). Usada apenas para localizar/contextualizar status e capacidade, nunca para citar valor numérico publicado. | Global Energy Monitor, GEM Wiki, "[Nome da mina]", [data de acesso], CC BY-NC-SA 4.0 | 2026-09-11 |
| SEC EDGAR — Rio Tinto plc Form 6-K "Operations Review" (CIK 0000863064) | https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000863064&type=6-K ; documentos localizados via EDGAR full text search (efts.sec.gov) | "Website Dissemination" — https://www.sec.gov/about/privacy-information (mesma base legal do regulador que a linha da Vale, acima) | A | Mesma exigência de `User-Agent` com contato real da linha acima. Os exhibits trimestrais "Operations Review" reportam produção de Benga (Moatize Basin) em duas tabelas com o mesmo percentual de participação declarado mas valores diferentes para o mesmo trimestre (ver nota em `data/provenance_parts/economia_producao.md`) — por isso, mesmo sendo nível A, nenhum valor anual único é publicado sem reconciliação. | Rio Tinto plc, Form 6-K "[título do exhibit]", SEC EDGAR, CIK 0000863064 | 2026-09-11 |

### Reexecução A2b/T2 (2026-09-11)

Confirmado, contra os 16 Form 20-F reais e os 3 exhibits 6-K reais já
espelhados em `data/raw/`: nível A mantido para SEC EDGAR (Vale e Rio
Tinto) — nenhuma mudança de nível. A extração passou a citar, por linha do
CSV, qual parser HTML leu o arquivo (`FLAVOR_USADO`, ver
`pipeline/00_fetch/fetch_vale_20f.py`), e a registrar no próprio CSV (coluna
`nota`) os dois defeitos de diagramação encontrados nos filings primários
(cabeçalho duplicado no 20-F do exercício 2019; duas tabelas conflitantes
para Benga no 6-K 4Q2012/FY2012 da Rio Tinto) — ver detalhe em
`data/provenance_parts/economia_producao.md`. Nenhuma fonte nova foi
adicionada ou reclassificada nesta tarefa.

<!-- SECAO_ECONOMIA_PRODUCAO_FIM -->
