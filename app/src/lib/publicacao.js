// Metadados de publicação (§6-A, CLAUDE.md). Única fonte de verdade para a URL do
// site, a URL do repositório, o DOI (quando existir) e a referência ABNT do conjunto
// (dados, painel interativo e artigo). `app/vite.config.js` e
// `app/scripts/inject-site-url.mjs` importam SITE_URL daqui em vez de repetir o valor.
export const SITE_URL = "https://Damnielps.github.io/moatize-geo-estimates";
export const REPO_URL = "https://github.com/Damnielps/moatize-geo-estimates";

/** DOI conceitual do Zenodo (todas as versões); preencher quando o Zenodo emitir a
 * primeira release arquivada — ver docs/CHECKLIST_PUBLICACAO.md. `null` até então. */
export const DOI = null;

export const VERSAO = "1.0.0";

export const AUTOR = {
  nome: "Daniel Pessini Sobreira",
  abnt: "SOBREIRA, Daniel Pessini",
  orcid: "0000-0002-6632-3991",
};

// Mesmo título de CITATION.cff — não redigir uma segunda versão aqui.
export const TITULO =
  "Urbanização induzida pela mineração em Tete e Moatize (Moçambique), 1997–2025";

/** Referência ABNT do conjunto (dados, painel interativo e artigo), PT ou EN. */
export function referenciaAbnt(lang = "pt") {
  if (lang === "en") {
    const acesso = DOI ? `DOI: ${DOI}.` : `Available at: ${SITE_URL}.`;
    return `${AUTOR.abnt}. ${TITULO}: data, interactive dashboard and article. Version ${VERSAO}. [S. l.], 2026. ${acesso}`;
  }
  const acesso = DOI ? `DOI: ${DOI}.` : `Disponível em: ${SITE_URL}.`;
  return `${AUTOR.abnt}. ${TITULO}: dados, painel interativo e artigo. Versão ${VERSAO}. [S. l.], 2026. ${acesso}`;
}
