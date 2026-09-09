import { createContext, useContext, useState, useCallback } from "react";

// Bilinguismo PT (padrão) / EN — CLAUDE.md §6.7. Dicionário estático, sem serviço de
// tradução externo (nenhuma chave de API).
export const DICIONARIO = {
  pt: {
    titulo_app: "Tete–Moatize · urbanização e mineração 1997–2025",
    nav_mapa: "Mapa",
    nav_populacao: "População",
    nav_graficos: "Gráficos",
    nav_narrativa: "Narrativa",
    nav_artigo: "Artigo",
    nav_metodologia: "Metodologia",
    ano: "Ano",
    unidade: "Unidade",
    camadas: "Camadas",
    camada_urbano: "Urbano (construído)",
    camada_industrial: "Pegada industrial/minerária",
    camada_reassentamento: "Pegada de reassentamento",
    camada_cultivo_irrigado: "Cultivo irrigado / vazante",
    camada_cultivo_sequeiro: "Vegetação sazonal (não confirmada como cultivo)",
    camada_agua: "Água",
    camada_varzea: "Várzea (estática)",
    camada_osm_vias: "Rodovias (N7 e demais, OSM)",
    camada_osm_ferrovia: "Ferrovia (linha do Sena, OSM)",
    camada_osm_lugares: "Topônimos (OSM)",
    camada_osm_aerodromo: "Aeródromo de Tete — TET/FQTT (OSM)",
    camada_adensamento_2020_2025: "Adensamento 2020→2025 (modelado, concordância de 3 sinais)",
    aviso_adensamento_selo:
      "Camada MODELADA (ADR 0016): síntese de concordância entre classificação própria, tendência de luz noturna (proxy de atividade, NÃO de população) e resíduo de edificações (Open Buildings, janela real 2020→~2023, não 2020→2025). A classe “adensando” não pode ser somada a “expansão nova” — são respostas distintas.",
    aviso_adensamento_sensibilidade_prefixo: "Sensibilidade a ±1 decil dos cortes: razão",
    aviso_adensamento_riscos:
      "A área de “adensando” NÃO é publicável como número exato — só como padrão espacial e ordem de grandeza. A camada não detecta esvaziamento/desadensamento (o sinal só pode subir, por construção).",
    aviso_adensamento_sem_manifesto: "(ressalvas completas indisponíveis — manifest.json não carregado)",
    aviso_urbano_comissao:
      "Atenção: entre 37% e 71% do que este mapa chama de “urbano” não é construído — é a comissão medida ano a ano (37,5% em 2025, 71,4% em 2010), ver ADR 0009 e a reexecução do ADR 0014. A camada nunca pode diminuir entre anos por construção (catraca R2, ADR 0013).",
    aviso_sequeiro:
      "Vegetação de fenologia sazonal acentuada, NÃO confirmada como cultivo (acurácia do usuário medida = 0,000; ADR 0012).",
    modo_comparacao: "Comparar com referência (swipe)",
    referencia: "Produto de referência",
    nenhuma: "Nenhuma",
    churn_titulo: "Instabilidade entre este ano e o anterior",
    baixar_dados: "Baixar dados (CSV/GeoJSON) com citação",
    fonte: "Fonte",
    metodo: "Método",
    selo: "Selo",
    ano_dado: "Ano do dado",
    nivel: "Nível de confiança",
    fechar: "Fechar",
    veredito_causal_titulo: "Veredito do desenho causal (Fase 3)",
    veredito_aviso:
      "As quatro quebras testadas (2005, 2011, 2016, 2022) têm contrafactual NÃO SUSTENTADO ou não estimável. Nenhuma leitura causal é sustentada por este estudo.",
    decomposicao_aviso:
      "A queda de 2022 NÃO pode ser atribuída à mina (ADR 0015, decisão 4). A decomposição não é partição: publica-se piso e teto, nunca um único valor.",
    aviso_ic_acuracia:
      "A acurácia do usuário vem com IC95 de ±0,20 e a classe ocupa 0,5–1,9 % da AOI. Nenhum dos 15 pares de anos-âncora tem IC95 que deixe de se sobrepor: a variação entre anos (0,286 em 2010 a 0,625 em 2025) NÃO é distinguível de ruído amostral. Leia como uma faixa única para toda a série, nunca como melhora ou piora ao longo do tempo (§10, ADR 0009).",
    piso_p_aviso:
      "Piso aritmético da inferência: com 1 unidade tratada e 5 doadoras, a inferência por permutação tem p mínimo possível = 1/6 ≈ 0,167 — nenhum resultado deste estudo pode atingir significância convencional (p < 0,05), não por fraqueza do efeito, mas por aritmética do pool de comparação. Um p perto de 0,167 é o piso do teste, não um resultado nulo comum: leia sempre junto com o piso, nunca isolado.",
    p_permutacao_titulo:
      "p por permutação (contra o piso aritmético de 1/6 ≈ 0,167; ver aviso acima)",
    anel_periurbano_ausente:
      "Anéis periurbanos por ano-âncora e modo de transições cultivo→construído ainda não existem em data/processed/ (§4.0: sem o dado, o app não o inventa). O logit espacial de conversão está registrado como NÃO DETERMINÁVEL nesta rodada (causal/logit_conversao_status.csv): o churn de 31–54% entre anos-âncora consecutivos (ADR 0013) torna 'este pixel mudou' um desfecho não identificável sem classe de origem estável. As camadas de cultivo abaixo mostram o estado de cada ano-âncora isoladamente, nunca uma transição inferida.",
    skip_link: "Pular para o conteúdo",
    metod_ambiente_titulo: "Ambiente e bibliotecas (§6-A.2)",
    metod_adr_titulo: "Decisões metodológicas — ADR (§6-A.5)",
    metod_provenance_titulo: "Proveniência (PROVENANCE.md)",
    metod_audit_titulo: "Auditoria de dados (data/DATA_AUDIT.md)",
    kpi_demografia: "Demografia / forma urbana",
    kpi_area_construida: "Área construída (AOI)",
    kpi_pegada: "Pegada industrial/reassentamento",
    kpi_agricultura: "Agricultura urbana e periurbana",
    kpi_acuracia: "Acurácia da classe \"construído\" (ADR 0009)",
    kpi_sem_linhas: "Sem linhas em stats_by_year_by_unit.csv para esta unidade/ano.",
    veredicto_secao_titulo: "O que os dados não sustentam",

    // --- Aba População (demografia_serie_1997_2025.csv) ---
    pop_titulo: "População — séries por unidade, 1997–2025",
    pop_aviso_titulo: "Como ler estas séries",
    pop_aviso_niveis:
      "Cada ponto tem nível de fonte A, B ou C (§4.0); o nível está no tooltip de cada valor. Pontos de nível B/C aparecem com marcador vazado nos gráficos.",
    pop_aviso_2025:
      "2025 é projeção geométrica institucional do INE, não recontagem censitária — selo “modelado”.",
    pop_aviso_moatize_limites:
      "O Distrito de Moatize mudou de limites administrativos entre censos: a comparabilidade entre 1997/2007/2017 NÃO é garantida.",
    pop_aviso_2017_naoajustado:
      "Os valores de 2017 são a contagem residente NÃO ajustada pela sub-enumeração estimada pelo INE — duas taxas de unidades diferentes, não uma faixa de incerteza de uma só grandeza: 3,7% a nível nacional (Moçambique); 3,8% na Província de Tete, unidade que aqui é pertinente para Cidade de Tete e Distrito de Moatize.",
    pop_aviso_total_nacional:
      "O total nacional publicado aqui é a soma dos ADM2 do COD-PS, e diverge do total do INE em +3 pessoas — leia o valor exato no CSV, não o digite.",
    // Molde com marcadores {piso} {teto} {desvioMin} {desvioMax} {desvioSemPeso} —
    // preenchidos em DemografiaPage.jsx a partir de
    // data/processed/populacao_vila_moatize_sensibilidade.csv, nunca escritos aqui.
    pop_aviso_vila_moatize:
      "A Vila de Moatize não tem contagem própria em fonte aberta: o valor de 2017 é o TETO de uma banda ({piso}–{teto}), estimado sobre a grade GRID3, não um valor central. A validação do mesmo método na Cidade de Tete mostrou que restringir a grade pela máscara de construído perde {desvioMin} a {desvioMax} das pessoas; só a soma sem peso validou ({desvioSemPeso}), e ela inclui área rural. Um único ano — sem série, sem CAGR. Ver docs/ADR/0017.",
    pop_indice_titulo: "Índice de crescimento (base = primeiro ano disponível de cada unidade)",
    pop_cagr_titulo: "CAGR por intervalo censitário",
    pop_ritmo_titulo: "Ritmo relativo — CAGR(unidade) ÷ CAGR(Moçambique)",
    pop_ritmo_metodo: "Razão simples entre o CAGR da unidade e o CAGR nacional no mesmo intervalo. Valor > 1: a unidade cresce mais rápido que o país nesse intervalo.",
    pop_tabela_titulo: "Tabela — unidade × ano",
    pop_moatize_vila_ausente_titulo: "Vila de Moatize",
    pop_moatize_vila_ausente_texto:
      "A vila-sede de Moatize (posto administrativo, nível ADM3) ainda não tem série própria neste CSV. O COD-PS (fonte A usada aqui) só publica população a nível ADM2 (distrito); a coleta complementar por WorldPop está em curso e pode não ter concluído nesta rodada. Esta linha permanece até o CSV trazer a unidade — não é omitida em silêncio.",
    pop_nivel_curto: "nível",
  },
  en: {
    titulo_app: "Tete–Moatize · urbanization and mining 1997–2025",
    nav_mapa: "Map",
    nav_populacao: "Population",
    nav_graficos: "Charts",
    nav_narrativa: "Narrative",
    nav_artigo: "Article",
    nav_metodologia: "Methodology",
    ano: "Year",
    unidade: "Unit",
    camadas: "Layers",
    camada_urbano: "Urban (built-up)",
    camada_industrial: "Industrial/mining footprint",
    camada_reassentamento: "Resettlement footprint",
    camada_cultivo_irrigado: "Irrigated / flood-recession cropping",
    camada_cultivo_sequeiro: "Seasonal vegetation (not confirmed as cropland)",
    camada_agua: "Water",
    camada_varzea: "Floodplain (static)",
    camada_osm_vias: "Roads (N7 and others, OSM)",
    camada_osm_ferrovia: "Railway (Sena line, OSM)",
    camada_osm_lugares: "Place names (OSM)",
    camada_osm_aerodromo: "Tete aerodrome — TET/FQTT (OSM)",
    camada_adensamento_2020_2025: "Densification 2020→2025 (modeled, 3-signal agreement)",
    aviso_adensamento_selo:
      "MODELED layer (ADR 0016): synthesis of agreement between own classification, night-light trend (proxy of activity, NOT population), and building-footprint residual (Open Buildings, real window 2020→~2023, not 2020→2025). The “densifying” class cannot be added to “new expansion” — they are distinct answers.",
    aviso_adensamento_sensibilidade_prefixo: "Sensitivity to ±1 decile of cutoffs: ratio",
    aviso_adensamento_riscos:
      "The “densifying” area is NOT publishable as an exact number — only as spatial pattern and order of magnitude. The layer does not detect emptying/de-densification (the signal can only rise, by construction).",
    aviso_adensamento_sem_manifesto: "(full caveats unavailable — manifest.json not loaded)",
    aviso_urbano_comissao:
      "Warning: between 37% and 71% of what this map calls “urban” is not built-up — the commission error measured year by year (37.5% in 2025, 71.4% in 2010); see ADR 0009 and the re-run in ADR 0014. The layer can never decrease between years by construction (R2 ratchet, ADR 0013).",
    aviso_sequeiro:
      "Vegetation with strong seasonal phenology, NOT confirmed as cropland (measured user's accuracy = 0.000; ADR 0012).",
    modo_comparacao: "Compare with reference (swipe)",
    referencia: "Reference product",
    nenhuma: "None",
    churn_titulo: "Instability between this year and the previous one",
    baixar_dados: "Download data (CSV/GeoJSON) with citation",
    fonte: "Source",
    metodo: "Method",
    selo: "Stamp",
    ano_dado: "Data year",
    nivel: "Confidence level",
    fechar: "Close",
    veredito_causal_titulo: "Causal design verdict (Phase 3)",
    veredito_aviso:
      "All four tested breaks (2005, 2011, 2016, 2022) have an UNSUPPORTED or non-estimable counterfactual. No causal reading is supported by this study.",
    decomposicao_aviso:
      "The 2022 drop CANNOT be attributed to the mine (ADR 0015, decision 4). The decomposition is not a partition: floor and ceiling are published, never a single value.",
    aviso_ic_acuracia:
      "User accuracy carries a ±0.20 95% CI and the class covers 0.5–1.9 % of the AOI. None of the 15 anchor-year pairs has non-overlapping CIs: the variation across years (0.286 in 2010 to 0.625 in 2025) is NOT distinguishable from sampling noise. Read it as a single band for the whole series, never as improvement or decline over time (§10, ADR 0009).",
    piso_p_aviso:
      "Arithmetic floor of inference: with 1 treated unit and 5 donors, permutation inference has a minimum possible p = 1/6 ≈ 0.167 — no result in this study can reach conventional significance (p < 0.05), not because the effect is weak, but because of the arithmetic of the comparison pool. A p near 0.167 is the test's floor, not an ordinary null result: always read it together with the floor, never in isolation.",
    p_permutacao_titulo:
      "Permutation p-value (against the arithmetic floor of 1/6 ≈ 0.167; see warning above)",
    anel_periurbano_ausente:
      "Per-year periurban rings and a cropland→built-up transition mode do not yet exist in data/processed/ (§4.0: without the data, the app does not invent it). The spatial conversion logit is recorded as NOT DETERMINABLE in this round (causal/logit_conversao_status.csv): 31–54% churn between consecutive anchor years (ADR 0013) makes 'this pixel changed' a non-identifiable outcome without a stable origin class. The cropland layers below show each anchor year in isolation, never an inferred transition.",
    skip_link: "Skip to content",
    metod_ambiente_titulo: "Environment and libraries (§6-A.2)",
    metod_adr_titulo: "Methodological decisions — ADR (§6-A.5)",
    metod_provenance_titulo: "Provenance (PROVENANCE.md)",
    metod_audit_titulo: "Data audit (data/DATA_AUDIT.md)",
    kpi_demografia: "Demography / urban form",
    kpi_area_construida: "Built-up area (AOI)",
    kpi_pegada: "Industrial/resettlement footprint",
    kpi_agricultura: "Urban and periurban agriculture",
    kpi_acuracia: "Accuracy of the \"built-up\" class (ADR 0009)",
    kpi_sem_linhas: "No rows in stats_by_year_by_unit.csv for this unit/year.",
    veredicto_secao_titulo: "What the data does not support",

    // --- Population tab (demografia_serie_1997_2025.csv) ---
    pop_titulo: "Population — series by unit, 1997–2025",
    pop_aviso_titulo: "How to read these series",
    pop_aviso_niveis:
      "Every point has a source level A, B or C (§4.0); the level is in each value's tooltip. B/C-level points render with a hollow marker on the charts.",
    pop_aviso_2025:
      "2025 is an institutional geometric projection by INE, not a census recount — stamped “modeled”.",
    pop_aviso_moatize_limites:
      "Distrito de Moatize changed administrative boundaries between censuses: comparability across 1997/2007/2017 is NOT guaranteed.",
    pop_aviso_2017_naoajustado:
      "2017 values are the residents count NOT adjusted for the under-enumeration estimated by INE — two rates for two different units, not an uncertainty band on a single quantity: 3.7% nationally (Mozambique); 3.8% in Tete Province, the unit relevant here for Cidade de Tete and Distrito de Moatize.",
    pop_aviso_total_nacional:
      "The national total published here is the sum of COD-PS ADM2 units, and diverges from INE's total by +3 people — read the exact value from the CSV, do not type it.",
    // Template with markers {piso} {teto} {desvioMin} {desvioMax} {desvioSemPeso} —
    // filled in DemografiaPage.jsx from
    // data/processed/populacao_vila_moatize_sensibilidade.csv, never written here.
    pop_aviso_vila_moatize:
      "Moatize town has no count of its own in any open source: the 2017 figure is the CEILING of a band ({piso}–{teto}) estimated over the GRID3 grid, not a central value. Cross-validating the same method on Tete city showed that restricting the grid by a built-up mask loses {desvioMin} to {desvioMax} of the people; only the unweighted sum validated ({desvioSemPeso}), and it includes rural area. A single year — no series, no CAGR. See docs/ADR/0017.",
    pop_indice_titulo: "Growth index (base = first available year per unit)",
    pop_cagr_titulo: "CAGR by census interval",
    pop_ritmo_titulo: "Relative pace — CAGR(unit) ÷ CAGR(Mozambique)",
    pop_ritmo_metodo: "Simple ratio between the unit's CAGR and the national CAGR for the same interval. Value > 1: the unit grows faster than the country in that interval.",
    pop_tabela_titulo: "Table — unit × year",
    pop_moatize_vila_ausente_titulo: "Moatize town (vila)",
    pop_moatize_vila_ausente_texto:
      "The Moatize town seat (administrative post, ADM3 level) does not yet have its own series in this CSV. COD-PS (the level-A source used here) only publishes population at ADM2 (district) level; the complementary WorldPop collection is in progress and may not have finished this round. This row stays until the CSV brings the unit — it is never silently omitted.",
    pop_nivel_curto: "level",
  },
};

const I18nContext = createContext(null);

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem("lang") || "pt");
  const t = useCallback((key) => DICIONARIO[lang]?.[key] ?? DICIONARIO.pt[key] ?? key, [lang]);
  const toggleLang = useCallback(() => {
    setLang((l) => {
      const novo = l === "pt" ? "en" : "pt";
      localStorage.setItem("lang", novo);
      return novo;
    });
  }, []);
  return (
    <I18nContext.Provider value={{ lang, t, toggleLang }}>{children}</I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n precisa de I18nProvider");
  return ctx;
}

// Divide um molde de i18n com marcadores "{chave}" em fragmentos alternados de texto
// e os nós React fornecidos em `partes[chave]` (ex.: um <ProvenanciaNumero>). Nunca
// formata número: só recorta a string em torno de valores já formatados por quem
// chama. Marcador sem parte correspondente é mantido literal (falha visível, não
// omissão silenciosa).
export function interpolarComPartes(molde, partes) {
  const regex = /\{(\w+)\}/g;
  const nos = [];
  let ultimo = 0;
  let m;
  let i = 0;
  while ((m = regex.exec(molde))) {
    if (m.index > ultimo) nos.push(molde.slice(ultimo, m.index));
    nos.push(
      Object.prototype.hasOwnProperty.call(partes, m[1]) ? (
        <span key={`${m[1]}-${i++}`}>{partes[m[1]]}</span>
      ) : (
        m[0]
      )
    );
    ultimo = regex.lastIndex;
  }
  if (ultimo < molde.length) nos.push(molde.slice(ultimo));
  return nos;
}
