// Resolvedor dos marcadores `{nome}` de app/src/content/narrativa.json (Fase 4b, B3).
//
// Porte da MESMA lógica do resolvedor de referência em Python que o portão de conteúdo
// usou (100/100 marcadores): filtro coluna a coluna (número comparado como número, texto
// como texto exato), `filtro_excluir`, estatísticas `valor unico` / `maximo` / `minimo` /
// `contagem` / `derivado` / `marco`, transformações `complemento_pct` e `fracao_para_pct`,
// derivados `diferenca` / `razao` / `variacao_pct` sobre marcadores do MESMO bloco.
// A gramática está na chave raiz `convencoes_marcadores` do próprio JSON.
//
// Nenhum número nasce aqui: todo valor vem de uma linha de CSV publicado em
// data/processed/ (copiado para app/public/data/ por scripts/sync-data.mjs) ou de
// data/processed/app/marcos.json. Filtro que não devolve exatamente uma linha em
// `valor unico` ⇒ `erro` preenchido e texto "—"; quem renderiza mostra o erro em
// desenvolvimento e o traço com aviso em produção. Nunca um número de reserva.
import { carregarCsv, carregarJson } from "./data.js";
import { piorSelo, piorNivel } from "./selos.js";
import { localeDoIdioma } from "./formato.js";

const TRACO = "—";
const ESPACO_FINO = "\u2009";
const ESPACO_DURO = "\u00A0";
const MENOS = "\u2212";

/** Caminho em app/public/data/ de um CSV declarado relativo a data/processed/. */
export function caminhoPublico(csv) {
  // sync-data.mjs: CSVs da raiz de data/processed/ vão para `csv/`; subpastas
  // (`causal/`, `economia/`) mantêm o nome da subpasta.
  return csv.includes("/") ? csv : `csv/${csv}`;
}

// Proveniência dos CSVs que NÃO trazem colunas `fonte`/`metodo` por linha. Só texto
// descritivo (nenhum número): nome do produto, do método e do ADR que o governa, na
// mesma redação que PainelEstatisticas.jsx já usa para esses artefatos. Quando a linha
// tem `fonte`/`metodo`/`nivel_fonte`, a linha vence.
const PROVENIENCIA_CSV = {
  "area_construida_por_ano.csv": {
    fonte: {
      pt: "Classificação própria (Landsat C2 L2 / Sentinel-2 L2A), regras R1 e R2",
      en: "Own classification (Landsat C2 L2 / Sentinel-2 L2A), rules R1 and R2",
    },
    metodo: {
      pt: "compostos de estação seca, classificador por ano, área em EPSG:32736 fora das pegadas (ADR 0011, 0013)",
      en: "dry-season composites, per-year classifier, area in EPSG:32736 outside the footprints (ADR 0011, 0013)",
    },
    nivel: "A",
  },
  "pegada_por_ano.csv": {
    fonte: {
      pt: "Classificação própria (Landsat C2 L2 / Sentinel-2 L2A); referência externa Maus et al. v2",
      en: "Own classification (Landsat C2 L2 / Sentinel-2 L2A); external reference Maus et al. v2",
    },
    metodo: {
      pt: "pegada por assinatura de solo/rocha exposto persistente dentro do envelope de busca (ADR 0011); sem regra de permanência (ADR 0014)",
      en: "footprint by persistent bare soil/rock signature within the search envelope (ADR 0011); no persistence rule (ADR 0014)",
    },
    nivel: "A",
  },
  "acuracia_por_ano.csv": {
    fonte: {
      pt: "Validação própria, estimador de Olofsson et al. (2014)",
      en: "Own validation, Olofsson et al. (2014) estimator",
    },
    metodo: {
      pt: "acurácia do usuário da classe construído, amostra estratificada pelo mapa; rótulos por interpretação visual automatizada (ADR 0009)",
      en: "user's accuracy of the built-up class, sample stratified by the map; labels by automated visual interpretation (ADR 0009)",
    },
    nivel: "A",
  },
  "causal/veredito_fase3.csv": {
    fonte: {
      pt: "Veredito da Fase 3: controle sintético, séries interrompidas e placebos contra as capitais de comparação",
      en: "Phase 3 verdict: synthetic control, interrupted time series and placebos against the comparison capitals",
    },
    metodo: {
      pt: "contagem de linhas do bloco de critérios, com critérios de rejeição fixados antes da série de luz (ADR 0015)",
      en: "row count of the criteria block, with rejection criteria fixed before the light series (ADR 0015)",
    },
    nivel: null,
  },
  "causal/serie_luzes_anual.csv": {
    fonte: { pt: null, en: null }, // a linha traz `fonte`
    metodo: {
      pt: "soma anual de radiância NPP-VIIRS-like no recorte fixo da área de estudo (EMENDA E6); a parte da Cidade de Tete é a interseção com o ADM2",
      en: "annual NPP-VIIRS-like radiance sum over the fixed study-area rectangle (EMENDA E6); the Tete city part is the intersection with the ADM2",
    },
    nivel: null,
  },
  "causal/cenarios_2035_2040.csv": {
    fonte: {
      pt: "Cenários da Fase 3 sobre a base do INE (projeção 2025)",
      en: "Phase 3 scenarios over the INE base (2025 projection)",
    },
    metodo: { pt: null, en: null }, // a linha traz `premissa_taxa`
    nivel: null,
  },
};

const DESCRICAO_OP = {
  diferenca: { pt: "diferença", en: "difference" },
  razao: { pt: "razão", en: "ratio" },
  variacao_pct: { pt: "variação percentual", en: "percent change" },
};

function numerico(v) {
  if (typeof v === "number") return Number.isFinite(v);
  if (typeof v !== "string" || v.trim() === "") return false;
  return /^-?\d+(\.\d+)?([eE][-+]?\d+)?$/.test(v.trim());
}

// Igualdade coluna a coluna: número como número (2021 casa com "2021" e "2021.0"),
// texto como texto exato. Coluna ausente na linha ⇒ não casa.
function casa(linha, filtro) {
  for (const [k, v] of Object.entries(filtro ?? {})) {
    const rv = linha[k];
    if (rv === undefined || rv === null) return false;
    if (numerico(rv) && numerico(v)) {
      if (Number(rv) !== Number(v)) return false;
    } else if (String(rv) !== String(v)) {
      return false;
    }
  }
  return true;
}

function filtrar(linhas, filtro, excluir) {
  let out = linhas.filter((l) => casa(l, filtro));
  if (excluir && Object.keys(excluir).length) out = out.filter((l) => !casa(l, excluir));
  return out;
}

function aplicarTransformacao(val, transf) {
  if (transf === "complemento_pct") return 100 * (1 - Number(val));
  if (transf === "fracao_para_pct") return 100 * Number(val);
  if (transf) throw new Error(`transformacao desconhecida '${transf}'`);
  return val;
}

// ---------------------------------------------------------------------------
// Formatos (convencoes_marcadores.formato). PT: convenção de Moçambique (pt-MZ: espaço de
// milhar, vírgula decimal), a mesma de lib/formato.js e de paper/FATOS_VERIFICADOS.md;
// EN: vírgula de milhar e ponto decimal.
// ---------------------------------------------------------------------------

function nf(v, lang, casas, opts = {}) {
  return new Intl.NumberFormat(localeDoIdioma(lang), {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
    ...opts,
  }).format(v);
}

function sufixoPct(lang) {
  return lang === "en" ? "%" : `${ESPACO_FINO}%`;
}

export function formatarMarcador(valor, formato, lang) {
  if (valor === null || valor === undefined) return TRACO;
  if (formato === "ano") return String(valor).slice(0, 4);
  const v = Number(valor);
  if (!Number.isFinite(v)) return String(valor);
  switch (formato) {
    case "inteiro":
      return nf(Math.round(v), lang, 0, { useGrouping: true });
    case "decimal1":
      return nf(v, lang, 1);
    case "pct0":
      return nf(v, lang, 0) + sufixoPct(lang);
    case "pct1":
      return nf(v, lang, 1) + sufixoPct(lang);
    case "pct1_abs":
      return nf(Math.abs(v), lang, 1) + sufixoPct(lang);
    case "pct1_sinal": {
      const abs = nf(Math.abs(v), lang, 1);
      // Sinal só depois de arredondar: -0,04 vira "0,0", sem sinal espúrio.
      const zero = Number(nf(Math.abs(v), "en", 1)) === 0;
      const sinal = zero ? "" : v > 0 ? "+" : MENOS;
      return sinal + abs + sufixoPct(lang);
    }
    case "km2_1":
      return `${nf(v, lang, 1)}${ESPACO_DURO}km²`;
    case "km2_2":
      return `${nf(v, lang, 2)}${ESPACO_DURO}km²`;
    default:
      throw new Error(`formato desconhecido '${formato}'`);
  }
}

// ---------------------------------------------------------------------------
// Carga das fontes: todos os CSVs citados pelos blocos (marcadores e séries de KPI)
// e marcos.json, uma vez.
// ---------------------------------------------------------------------------

function blocosDe(narrativa) {
  const blocos = [{ id: "topo", bloco: narrativa.topo }];
  for (const k of narrativa.topo?.kpis ?? []) blocos.push({ id: `kpi:${k.id}`, bloco: k });
  for (const c of narrativa.capitulos ?? []) blocos.push({ id: `cap:${c.id}`, bloco: c });
  return blocos;
}

export async function carregarFontesNarrativa(narrativa) {
  const csvs = new Set();
  for (const { bloco } of blocosDe(narrativa)) {
    for (const m of bloco.marcadores ?? []) if (m.csv) csvs.add(m.csv);
    for (const s of bloco.serie ?? []) if (s.csv) csvs.add(s.csv);
  }
  const lista = [...csvs];
  const [tabelas, marcosJson] = await Promise.all([
    Promise.all(lista.map((c) => carregarCsv(caminhoPublico(c)))),
    carregarJson("app/marcos.json"),
  ]);
  const porCsv = new Map(lista.map((c, i) => [c, tabelas[i]]));
  const marcos = new Map((marcosJson?.marcos ?? []).map((m) => [m.id, m]));
  return { porCsv, marcos };
}

// ---------------------------------------------------------------------------
// Resolução
// ---------------------------------------------------------------------------

function provenienciaLinha(csv, linha, lang) {
  const d = PROVENIENCIA_CSV[csv];
  const fonte = linha?.fonte ?? d?.fonte?.[lang] ?? d?.fonte?.pt ?? null;
  const metodo = linha?.metodo ?? linha?.premissa_taxa ?? d?.metodo?.[lang] ?? d?.metodo?.pt ?? null;
  const nivel = linha?.nivel_fonte ?? d?.nivel ?? null;
  return { fonte, metodo, nivel };
}

function notaArtefato(m, lang) {
  const partes = [];
  if (m.nota) partes.push(m.nota);
  if (m.csv) {
    const filtro = Object.entries(m.filtro ?? {})
      .map(([k, v]) => `${k}=${v}`)
      .join(", ");
    const excl = Object.entries(m.filtro_excluir ?? {})
      .map(([k, v]) => `${k}≠${v}`)
      .join(", ");
    const rot = lang === "en" ? "Artifact" : "Artefato";
    partes.push(
      `${rot}: data/processed/${m.csv} · ${m.coluna} · ${m.estatistica}` +
        (filtro ? ` · ${filtro}` : "") +
        (excl ? ` · ${excl}` : "") +
        (m.transformacao ? ` · ${m.transformacao}` : "")
    );
  }
  return partes.join(" ");
}

/**
 * Resolve todos os marcadores de UM bloco (topo, KPI ou capítulo). Devolve
 * `{ [nome]: { nome, valor, texto, fonte, metodo, selo, nivel_fonte, ano, nota, erro } }`.
 * `erro` não nulo ⇒ `valor` nulo e `texto` "—".
 */
export function resolverBloco(bloco, fontes, lang) {
  const porNome = new Map((bloco.marcadores ?? []).map((m) => [m.nome, m]));
  const cache = new Map();
  const pilha = new Set();

  function resolver(nome) {
    if (cache.has(nome)) return cache.get(nome);
    const m = porNome.get(nome);
    let r;
    try {
      if (!m) throw new Error(`marcador '${nome}' nao declarado no bloco`);
      if (pilha.has(nome)) throw new Error(`derivado circular em '${nome}'`);
      pilha.add(nome);
      r = resolverUm(m);
      pilha.delete(nome);
    } catch (e) {
      pilha.delete(nome);
      r = {
        nome,
        valor: null,
        texto: TRACO,
        fonte: null,
        metodo: null,
        selo: m?.selo ?? null,
        nivel_fonte: null,
        ano: null,
        nota: m ? notaArtefato(m, lang) : null,
        erro: e?.message ?? String(e),
      };
    }
    cache.set(nome, r);
    return r;
  }

  function resolverUm(m) {
    const est = m.estatistica;
    let valor;
    let fonte = null;
    let metodo = null;
    let nivel = null;
    let seloLinha = null;
    let ano = null;

    if (est === "marco") {
      const marco = fontes.marcos.get(m.marco);
      if (!marco) throw new Error(`marco '${m.marco}' nao encontrado em marcos.json`);
      valor = marco[m.campo];
      if (valor === null || valor === undefined || valor === "") {
        throw new Error(`campo '${m.campo}' vazio no marco '${m.marco}'`);
      }
      fonte = marco.fonte ?? null;
      metodo =
        lang === "en"
          ? `event date (${m.campo}) in config/marcos.yaml → data/processed/app/marcos.json`
          : `data do evento (${m.campo}) em config/marcos.yaml → data/processed/app/marcos.json`;
      nivel = marco.nivel ?? null;
      ano = String(valor).slice(0, 4);
    } else if (est === "derivado") {
      const d = m.derivado ?? {};
      const [ka, kb] =
        d.op === "variacao_pct" ? [d.de, d.para] : [d.a, d.b];
      const ra = resolver(ka);
      const rb = resolver(kb);
      if (ra.erro || rb.erro) {
        throw new Error(`derivado '${m.nome}' depende de marcador com erro (${ra.erro ?? rb.erro})`);
      }
      const a = Number(ra.valor);
      const b = Number(rb.valor);
      if (d.op === "diferenca") valor = a - b;
      else if (d.op === "razao") valor = a / b;
      else if (d.op === "variacao_pct") valor = 100 * (b / a - 1);
      else throw new Error(`operacao derivada desconhecida '${d.op}'`);
      if (!Number.isFinite(valor)) throw new Error(`derivado '${m.nome}' nao finito`);
      fonte = [...new Set([ra.fonte, rb.fonte].filter(Boolean))].join(" ; ") || null;
      const op = DESCRICAO_OP[d.op]?.[lang] ?? d.op;
      metodo =
        (lang === "en" ? `${op} between ` : `${op} entre `) +
        `{${ka}} ${lang === "en" ? "and" : "e"} {${kb}}` +
        ([ra.metodo, rb.metodo].filter(Boolean).length ? ` — ${[...new Set([ra.metodo, rb.metodo].filter(Boolean))].join(" ; ")}` : "");
      nivel = piorNivel(ra.nivel_fonte, rb.nivel_fonte);
      seloLinha = piorSelo(ra.selo, rb.selo);
      ano = [ra.ano, rb.ano].filter((x) => x != null).join("–") || null;
    } else {
      const linhas = fontes.porCsv.get(m.csv);
      if (!linhas) throw new Error(`CSV '${m.csv}' nao carregado`);
      const filtradas = filtrar(linhas, m.filtro, m.filtro_excluir);
      let origem = null;
      if (est === "valor unico") {
        if (filtradas.length !== 1) {
          throw new Error(
            `filtro devolveu ${filtradas.length} linhas (esperado 1) em ${m.csv} filtro=${JSON.stringify(m.filtro ?? {})}`
          );
        }
        origem = filtradas[0];
        const bruto = origem[m.coluna];
        if (bruto === undefined) throw new Error(`coluna '${m.coluna}' ausente em ${m.csv}`);
        if (bruto === null || bruto === "") throw new Error(`celula vazia em ${m.csv}.${m.coluna}`);
        valor = numerico(bruto) ? Number(bruto) : bruto;
      } else if (est === "maximo" || est === "minimo") {
        if (!filtradas.length) throw new Error(`nenhuma linha para ${est} em ${m.csv}`);
        const vals = filtradas.map((l) => Number(l[m.coluna]));
        if (vals.some((x) => !Number.isFinite(x))) throw new Error(`valor nao numerico em ${m.csv}.${m.coluna}`);
        valor = est === "maximo" ? Math.max(...vals) : Math.min(...vals);
        origem = filtradas[vals.indexOf(valor)];
      } else if (est === "contagem") {
        valor = filtradas.length;
        origem = null;
      } else {
        throw new Error(`estatistica desconhecida '${est}'`);
      }
      const p = provenienciaLinha(m.csv, origem ?? filtradas[0], lang);
      fonte = p.fonte;
      metodo = p.metodo;
      nivel = p.nivel;
      seloLinha = origem?.selo ?? null;
      ano = origem?.ano ?? null;
    }

    valor = aplicarTransformacao(valor, m.transformacao);
    const texto = formatarMarcador(valor, m.formato, lang);
    return {
      nome: m.nome,
      valor,
      texto,
      fonte,
      metodo,
      selo: m.selo ?? seloLinha ?? null,
      nivel_fonte: nivel,
      ano,
      nota: notaArtefato(m, lang) || null,
      erro: null,
    };
  }

  const out = {};
  for (const m of bloco.marcadores ?? []) out[m.nome] = resolver(m.nome);
  return out;
}

/** Série de sparkline de um KPI: cada ponto é um `valor unico`; falha ⇒ null + erro. */
export function resolverSerie(serie, fontes) {
  const valores = [];
  const erros = [];
  for (const p of serie ?? []) {
    const linhas = fontes.porCsv.get(p.csv) ?? [];
    const f = filtrar(linhas, p.filtro);
    const v = f.length === 1 ? Number(f[0][p.coluna]) : NaN;
    if (f.length !== 1 || !Number.isFinite(v)) {
      erros.push(`${p.csv} ${JSON.stringify(p.filtro)}: ${f.length} linhas`);
      valores.push(null);
    } else {
      valores.push(v);
    }
  }
  return { valores, anos: (serie ?? []).map((p) => p.ano), erros };
}

/** Todos os blocos resolvidos, com a contagem para verificação. */
export function resolverNarrativa(narrativa, fontes, lang) {
  const porBloco = {};
  let total = 0;
  let resolvidos = 0;
  const erros = [];
  for (const { id, bloco } of blocosDe(narrativa)) {
    const r = resolverBloco(bloco, fontes, lang);
    porBloco[id] = r;
    for (const x of Object.values(r)) {
      total += 1;
      if (x.erro) erros.push(`[${id}] ${x.nome}: ${x.erro}`);
      else resolvidos += 1;
    }
  }
  return { porBloco, total, resolvidos, erros };
}
