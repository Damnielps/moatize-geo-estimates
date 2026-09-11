// Utilitários para CSVs em formato longo (colunas:
// unidade_geografica,ano,variavel,valor,unidade_medida,selo,nivel_fonte,fonte,metodo,nota)
// — ex.: data/processed/demografia_serie_1997_2025.csv. Nada aqui inventa número: só
// filtra/lê o que já está no CSV carregado por carregarCsv() (data.js).

/** Uma linha específica (unidade, ano, variável) — ou undefined se não existir. */
export function pegar(linhas, unidade, ano, variavel) {
  return linhas.find(
    (r) => r.unidade_geografica === unidade && r.ano === ano && r.variavel === variavel
  );
}

/** Todas as linhas de (unidade, variável), ordenadas por ano. */
export function serie(linhas, unidade, variavel) {
  return linhas
    .filter((r) => r.unidade_geografica === unidade && r.variavel === variavel)
    .slice()
    .sort((a, b) => a.ano - b.ano);
}

// data/processed/causal/serie_luzes_anual.csv usa chaves internas em minúsculas, sem
// acento nem hífen, na coluna `unidade`: "tete_aoi" (recorte fixo da AOI, EMENDA E6) e as
// cinco cidades-controle. Os nomes de exibição seguem config/study.yaml
// (controles.incluidos). Todas as unidades são RETÂNGULOS fixos (EMENDA E6, docs/DESENHO_FASE3.md),
// não os distritos: o de Tete (`tete_aoi`, 2.494 km²) contém a Cidade de Tete, a vila de
// Moatize e a mina. Rotulá-lo "Cidade de Tete" atribuiria à cidade a luz da mina — por isso
// o rótulo nomeia a área de estudo. O rótulo por idioma fica em ROTULO_TETE_AOI.
const ROTULO_TETE_AOI = { pt: "Tete–Moatize (área de estudo)", en: "Tete–Moatize (study area)" };
const MAPA_UNIDADE_LUZ = {
  tete_aoi: ROTULO_TETE_AOI.pt,
  chimoio: "Chimoio",
  quelimane: "Quelimane",
  lichinga: "Lichinga",
  xaixai: "Xai-Xai",
  inhambane: "Inhambane",
};

/** Nome de exibição para a coluna `unidade` de serie_luzes_anual.csv; chave crua se desconhecida. */
export function unidadeLuz(unidade, lang = "pt") {
  if (unidade === "tete_aoi") return ROTULO_TETE_AOI[lang] ?? ROTULO_TETE_AOI.pt;
  return MAPA_UNIDADE_LUZ[unidade] ?? unidade;
}
