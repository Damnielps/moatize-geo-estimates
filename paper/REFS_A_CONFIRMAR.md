# Referências a confirmar — não citadas no texto

Regra (`CLAUDE.md` §7): toda referência é verificada por DOI ou URL institucional antes de entrar no
artigo. As que não puderam ser verificadas ficam aqui, com o motivo, e **não** aparecem em
`paper/artigo.md`. Verificação feita em 2026-09-08.

| Referência (como registrada no repositório) | Onde aparece no repositório | Motivo de não confirmação | O que foi usado no lugar |
|---|---|---|---|
| Esch, T., Heldens, W., Hirner, A., et al. (2022). World Settlement Footprint (WSF) Evolution — Mapping human presence on Earth with Landsat, Sentinel-1 and Sentinel-2 time series data. *Remote Sensing of Environment*, 287, 113453. DOI 10.1016/j.rse.2022.113453 | `data/provenance_parts/construida.md` (citação do WSF Evolution) | `https://doi.org/10.1016/j.rse.2022.113453` devolve **HTTP 404**; a busca web não localizou artigo com esse título, volume e número de artigo (localizou apenas o WSF 3D, RSE 270, 2022). Pode ser DOI errado, artigo não publicado sob esse título, ou volume/ano trocados. | Marconcini, Metz-Marconcini, Esch & Gorelick (2021), *GI_Forum* 9(1):33–38, DOI 10.1553/giscience2021_01_s33 — a citação exigida na página de licença do produtor — mais a página do dataset no DLR EOC Geoservice. |
| Sapa-AFP (2011), notícia sobre o reassentamento de ~1.300 famílias pela Vale | `CLAUDE.md` §8 (âncora factual) | Agência de notícias sem arquivo público estável; nenhuma URL primária localizada na Fase 0' (`data/provenance_parts/reassentamento.md`). | Human Rights Watch (2013), com as duas contagens internas do relatório (1.005 e 1.365) preservadas. |

## Referências verificadas apenas parcialmente (citadas com a ressalva indicada)

| Referência | Verificação obtida | Ressalva |
|---|---|---|
| Newey & West (1987), *Econometrica* 55(3):703–708 | Página da Econometric Society e registro JSTOR (stable/1913610) confirmam título, autores, volume e páginas; o JSTOR bloqueou a leitura do conteúdo. | Citada com a URL estável do JSTOR, sem DOI (o DOI 10.2307/1913610 resolve para o mesmo registro; o DOI 10.3386/T0055 devolvido por um agregador é o do *working paper* NBER, não do artigo). |
| Pesaresi & Politis (2023), GHS-BUILT-S R2023A | Catálogo de dados do JRC confirma título, autores, editor e versão; a página lista "2026" como ano de publicação na citação sugerida, enquanto o release é R2023A. | Citada com o ano do release (2023) e o DOI do catálogo; o ano de citação sugerido pelo catálogo pode divergir. |
| Mosca & Selemane (2011), CIP | Localizada em repositório de terceiros (Land Portal) e em cópia no Yumpu; a página do produtor (CIP) declara "todos os direitos reservados". | Citada como literatura (nível C para dados); a URL é a do Land Portal, não do produtor. |
| Global Energy Monitor, Global Coal Mine Tracker (agosto de 2026) | Página do produto confirmada; o download exige formulário. | Citada pela URL do produto; o valor "mothballed" para Moatize foi lido da wiki do GEM, que é agregador — usado apenas como contexto, não como número. |
