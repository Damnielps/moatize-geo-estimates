// Metadados de publicação (§6-A, CLAUDE.md). Única fonte de verdade para a URL do
// site, a URL do repositório, o DOI (quando existir) e a referência ABNT do conjunto
// (dados, painel interativo e artigo). `app/vite.config.js` e
// `app/scripts/inject-site-url.mjs` importam SITE_URL daqui em vez de repetir o valor.
export const SITE_URL = "https://Damnielps.github.io/moatize-geo-estimates";
export const REPO_URL = "https://github.com/Damnielps/moatize-geo-estimates";

/** DOI conceitual do Zenodo (todas as versões); preencher quando o Zenodo emitir a
 * primeira release arquivada — ver docs/CHECKLIST_PUBLICACAO.md. `null` até então. */
export const DOI = "10.5281/zenodo.22718197";

export const VERSAO = "1.0.0";

export const AUTOR = {
  nome: "Daniel Pessini Sobreira",
  abnt: "SOBREIRA, Daniel Pessini",
  orcid: "0000-0002-6632-3991",
};

// Mesmo título de CITATION.cff — não redigir uma segunda versão aqui.
export const TITULO =
  "Urbanização induzida pela mineração em Tete e Moatize (Moçambique), 1997–2025";

/**
 * Referência ABNT em duas partes: o corpo e a cláusula de acesso (DOI, ou a URL do
 * painel enquanto não houver DOI). Separar as duas existe para a tela poder transformar
 * só a cláusula de acesso em link — quando ela era concatenada e o link vinha depois, o
 * identificador aparecia duas vezes seguidas na citação.
 */
export function referenciaPartes(lang = "pt") {
  const en = lang === "en";
  const corpo = en
    ? `${AUTOR.abnt}. ${TITULO}: data, interactive dashboard and article. Version ${VERSAO}. [S. l.], 2026.`
    : `${AUTOR.abnt}. ${TITULO}: dados, painel interativo e artigo. Versão ${VERSAO}. [S. l.], 2026.`;
  const acesso = DOI
    ? { rotulo: `DOI: ${DOI}`, href: `https://doi.org/${DOI}` }
    : { rotulo: en ? `Available at: ${SITE_URL}` : `Disponível em: ${SITE_URL}`, href: SITE_URL };
  return { corpo, acesso };
}

/** A mesma referência como texto corrido — é o que o botão "Copiar" põe na área de
 * transferência, e o que vai para um gerenciador de referências. */
export function referenciaAbnt(lang = "pt") {
  const { corpo, acesso } = referenciaPartes(lang);
  return `${corpo} ${acesso.rotulo}.`;
}
