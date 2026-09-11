// Página "Província e cidades" (Fase 4b, tarefa B4). Desenho portado de
// urban-canaa/web/src/tabs/Economia.tsx (painel triplo empilhado com eixo x comum,
// marcos sombreados, KPIs, "Ver tabela") para JSX + Recharts. Consome só
// data/processed/ (via app/public/data/, publicado por scripts/sync-data.mjs). Nenhum
// número é digitado à mão: anos, bases de índice, unidades de medida e contagens saem
// de carregarCsv()/marcos.json, e todo valor passa por ProvenanciaNumero ou por um
// tooltip que mostra selo e nível da linha do CSV.
import { useEffect, useId, useMemo, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid, ReferenceArea, ReferenceLine,
  ResponsiveContainer,
} from "recharts";
import { carregarCsv } from "../lib/data.js";
import { unidadeLuz } from "../lib/series.js";
import { useMarcos } from "../lib/marcos.js";
import { useI18n, interpolarComPartes } from "../lib/i18n.jsx";
import { formatarNumero, localeDoIdioma } from "../lib/formato.js";
import { piorSelo, piorNivel, pontoPorNivel } from "../lib/selos.js";
import { Figura, Kpi, Secao, Segmentado, Tabela, Esqueleto, Erro } from "../components/ui.jsx";
import ProvenanciaNumero from "../components/ProvenanciaNumero.jsx";
import { TEXTOS, UNIDADES_CASCATA, UNIDADE_REFERENCIA, TIPOS_MARCO_FIG2 } from "../content/provincia.js";
import "../styles/provincia.css";

// Cores fixas por unidade (paleta Ardósia já usada no app); destaque = espessura do traço.
const COR_UNIDADE = {
  tete: "#24404F",
  moatize_distrito: "#9C5B41",
  moatize_vila: "#A98A3F",
  provincia: "#3D5A4C",
  mocambique: "#A9A6A0",
};
const CORES = ["#24404F", "#9C5B41", "#3D5A4C", "#A98A3F"];
const VAR_POP = "populacao_total_residente";
const RE_INDICE = /^indice_base_(\d{4})$/;
const RE_CAGR = /^cagr_(\d{4})_(\d{4})$/;

// Geometria comum dos três painéis da Figura 2: mesma largura de eixo Y e mesmas
// margens — é isso que alinha os anos verticalmente entre os painéis.
const LARG_EIXO_Y = 64;
const MARGEM_PAINEL = { top: 10, right: 16, bottom: 0, left: 0 };
// O painel superior ganha folga em cima para os rótulos das fases (só o topo muda:
// esquerda/direita, que alinham os anos, são iguais nos três).
const MARGEM_PAINEL_TOPO = { ...MARGEM_PAINEL, top: 22 };
const PASSO_TICK_ANOS = 5;

function vazio(v) {
  return v === null || v === undefined || v === "" || (typeof v === "number" && Number.isNaN(v));
}

function preencher(molde, partes) {
  return String(molde).replace(/\{(\w+)\}/g, (m, k) => (k in partes ? String(partes[k]) : m));
}

function anosTicks([ini, fim]) {
  const out = [];
  for (let a = ini; a <= fim; a += PASSO_TICK_ANOS) out.push(a);
  if (out[out.length - 1] !== fim) out.push(fim);
  return out;
}

// Largura de um elemento (ResizeObserver) — usada para decidir se os rótulos das fases
// cabem dentro do painel superior ou se ficam só na legenda abaixo.
function useLargura() {
  // Ref de callback: o nó só existe depois da carga dos CSV, então um useRef + efeito
  // de montagem nunca chegaria a observá-lo.
  const [no, setNo] = useState(null);
  const [largura, setLargura] = useState(0);
  useEffect(() => {
    if (!no || typeof ResizeObserver === "undefined") return undefined;
    const obs = new ResizeObserver(([e]) => setLargura(e.contentRect.width));
    obs.observe(no);
    return () => obs.disconnect();
  }, [no]);
  return [setNo, largura];
}

// Mini-série da KPI: pontos vazados para nível B/C. Vive só aqui (ui.jsx fora do escopo).
function MiniSerie({ pontos, cor }) {
  const dados = pontos.map((p) => ({ ano: p.ano, valor: p.valor, nivel: p.nivel }));
  if (dados.filter((d) => !vazio(d.valor)).length < 2) return null;
  return (
    <LineChart width={132} height={34} data={dados} margin={{ top: 4, right: 4, bottom: 2, left: 4 }}>
      <Line type="monotone" dataKey="valor" stroke={cor} strokeWidth={1.6} dot={pontoPorNivel("nivel", cor)} isAnimationActive={false} connectNulls />
    </LineChart>
  );
}

// Célula numérica de tabela "Ver tabela": o número passa por ProvenanciaNumero com a
// fonte/método/selo/nível da LINHA do CSV de onde saiu — nunca só o valor solto.
function CelulaProv({ linha, valor, formatador, metodo, nota, unidadeMedida }) {
  const v = valor !== undefined ? valor : linha?.valor;
  if (!linha || vazio(v)) return "—";
  return (
    <ProvenanciaNumero
      valor={v}
      formatador={formatador}
      unidadeMedida={unidadeMedida}
      fonte={linha.fonte}
      metodo={metodo ?? linha.metodo}
      ano={linha.ano}
      selo={linha.selo}
      nivelFonte={linha.nivel_fonte}
      nota={nota ?? linha.nota}
    />
  );
}

// Tooltip do Recharts com selo e nível de cada série, lidos da linha do CSV do ponto.
// Séries com o mesmo `name` (trecho sólido + trecho tracejado) aparecem uma vez.
function TooltipProv({ active, payload, label, linhaDe, formatador, unidade, T, t }) {
  if (!active || !payload?.length) return null;
  const vistos = new Set();
  const itens = [];
  for (const p of payload) {
    if (vazio(p.value) || vistos.has(p.name)) continue;
    vistos.add(p.name);
    itens.push({ p, linha: linhaDe(p.dataKey, p.payload) });
  }
  if (!itens.length) return null;
  return (
    <div className="provincia-tooltip">
      <strong>{label}</strong>
      {itens.map(({ p, linha }) => (
        <div key={p.name}>
          <span aria-hidden="true" style={{ color: p.color }}>■ </span>
          {p.name}: {formatador(p.value)}
          {unidade ? ` ${unidade}` : ""}
          {" · "}
          {linha ? (
            <>
              {t("selo")}: {T.selo_rotulos[linha.selo] ?? linha.selo ?? "—"} · {t("nivel")}: {linha.nivel_fonte ?? "—"}
            </>
          ) : (
            T.tooltip_sem_linha
          )}
        </div>
      ))}
    </div>
  );
}

// Motivo de ausência da produção em linguagem de leitor. Só o motivo técnico conhecido
// (coleta na SEC aguardando autorização) ganha a frase; qualquer outro motivo que o
// pipeline venha a publicar aparece como está no CSV, para a frase nunca mentir.
const RE_MOTIVO_SEC = /SEC_USER_AGENT/;

function unidadesDe(linhas) {
  return [...new Set((linhas ?? []).map((r) => r.unidade_medida).filter(Boolean))].join(" / ");
}

function LegendaHtml({ itens }) {
  return (
    <span className="provincia-legenda">
      {itens.map((i) => (
        <span key={i.rotulo} className="provincia-legenda__item">
          <span aria-hidden="true" className="provincia-legenda__traco" style={{ background: i.cor }} />
          {i.rotulo}
        </span>
      ))}
    </span>
  );
}

export default function ProvinciaPage() {
  const { lang, t } = useI18n();
  const T = TEXTOS[lang] ?? TEXTOS.pt;
  const { fases, censos, pontuais } = useMarcos();
  const idFig2 = useId();
  const [refPaineis, larguraPaineis] = useLargura();

  const [demografia, setDemografia] = useState(null);
  const [contexto, setContexto] = useState(null);
  const [luzes, setLuzes] = useState(null);
  const [preco, setPreco] = useState(null);
  const [producao, setProducao] = useState(null);
  const [contas, setContas] = useState(null);
  const [erro, setErro] = useState(null);

  const [unidadeChave, setUnidadeChave] = useState("tete");
  const [modoFig1, setModoFig1] = useState("absoluto");
  const [luzComparacao, setLuzComparacao] = useState("so_tete");
  const [verTabelaFig2, setVerTabelaFig2] = useState(false);

  useEffect(() => {
    Promise.all([
      carregarCsv("csv/demografia_serie_1997_2025.csv"),
      carregarCsv("csv/demografia_contexto_nao_nucleo.csv"),
      carregarCsv("causal/serie_luzes_anual.csv"),
      carregarCsv("economia/preco_carvao_anual.csv"),
      carregarCsv("economia/producao_moatize_anual.csv"),
      carregarCsv("economia/contas_regionais_tete.csv"),
    ])
      .then(([d, c, l, p, prod, ct]) => {
        setDemografia(d);
        setContexto(c);
        setLuzes(l);
        setPreco(p);
        setProducao(prod);
        setContas(ct);
      })
      .catch(setErro);
  }, []);

  const carregando = demografia === null && !erro;
  const todasUnidades = useMemo(() => [...UNIDADES_CASCATA, UNIDADE_REFERENCIA], []);
  const unidadeAtual = UNIDADES_CASCATA.find((u) => u.chave === unidadeChave) ?? UNIDADES_CASCATA[1];

  const fmtInt = (v) => (typeof v === "number" ? formatarNumero(v, lang, { max: 0 }) : "—");
  const fmtNum2 = (v) => (typeof v === "number" ? formatarNumero(v, lang, { max: 2 }) : "—");
  // Formato compacto por idioma para eixos ("36 mi" / "36M"): o eixo não corta rótulo.
  const fmtCompacto = useMemo(() => {
    const nf = new Intl.NumberFormat(localeDoIdioma(lang), { notation: "compact", maximumFractionDigits: 1 });
    return (v) => (typeof v === "number" ? nf.format(v) : "");
  }, [lang]);
  const nomeVariavel = (v) => T.variaveis?.[v] ?? v;
  const nomeUnidadeMedida = (u) => T.unidades_medida?.[u] ?? u;

  // --- linhas demográficas por unidade ---------------------------------------------
  const porUnidade = useMemo(() => {
    const m = {};
    for (const u of todasUnidades) {
      const linhas = (demografia ?? []).filter((r) => r.unidade_geografica === u.csv);
      const pop = linhas.filter((r) => r.variavel === VAR_POP).sort((a, b) => a.ano - b.ano);
      const indice = linhas.filter((r) => RE_INDICE.test(r.variavel)).sort((a, b) => a.ano - b.ano);
      const baseIndice = indice.length ? Number(indice[0].variavel.match(RE_INDICE)[1]) : null;
      const cagrs = linhas
        .filter((r) => RE_CAGR.test(r.variavel) && !vazio(r.valor))
        .map((r) => {
          const [, a, b] = r.variavel.match(RE_CAGR);
          return { intervalo: `${a}→${b}`, ordem: Number(a), row: r };
        })
        .sort((a, b) => a.ordem - b.ordem);
      m[u.chave] = { pop, indice, baseIndice, cagrs };
    }
    return m;
  }, [demografia, todasUnidades]);

  const anosFig1 = useMemo(
    () => [...new Set((demografia ?? []).filter((r) => r.variavel === VAR_POP).map((r) => r.ano))].filter((a) => typeof a === "number").sort((a, b) => a - b),
    [demografia]
  );

  // --- KPIs da unidade escolhida ----------------------------------------------------
  const kpis = useMemo(() => {
    const d = porUnidade[unidadeAtual.chave];
    if (!d) return null;
    const comValor = d.pop.filter((r) => !vazio(r.valor));
    // Projeção = último ponto, se modelado e posterior a outro ponto com valor. Um ponto
    // modelado único (Vila de Moatize) é a estimativa do ano, não uma projeção.
    const ultimo = comValor[comValor.length - 1] ?? null;
    const projecao = ultimo && ultimo.selo === "modelado" && comValor.length > 1 ? ultimo : null;
    const ultimoCenso = projecao ? comValor[comValor.length - 2] : ultimo;
    return {
      ultimoCenso,
      projecao,
      cagrs: d.cagrs,
      serie: d.pop.map((r) => ({ ano: r.ano, valor: vazio(r.valor) ? null : r.valor, nivel: r.nivel_fonte })),
    };
  }, [porUnidade, unidadeAtual]);

  // --- Figura 1: absolutos (cascata local) ou índice (todas as unidades) -------------
  const unidadesFig1 = useMemo(() => {
    if (modoFig1 === "indice") return todasUnidades;
    if (unidadeChave === "provincia") return UNIDADES_CASCATA.filter((u) => u.chave === "provincia");
    return UNIDADES_CASCATA.filter((u) => u.local);
  }, [modoFig1, unidadeChave, todasUnidades]);

  const linhasFig1De = (chave) => (modoFig1 === "indice" ? porUnidade[chave]?.indice : porUnidade[chave]?.pop) ?? [];

  // Trecho sólido até o último ponto não modelado; tracejado desse ponto ao modelado.
  const dadosFig1 = useMemo(() => {
    return anosFig1.map((ano) => {
      const linha = { ano, _linhas: {} };
      for (const u of unidadesFig1) {
        const rows = linhasFig1De(u.chave).filter((r) => !vazio(r.valor));
        const row = rows.find((r) => r.ano === ano) ?? null;
        const naoMod = rows.filter((r) => r.selo !== "modelado");
        const ultimoNaoMod = naoMod[naoMod.length - 1]?.ano;
        const v = row ? row.valor : null;
        linha[`${u.chave}_solido`] = row && row.selo !== "modelado" ? v : null;
        linha[`${u.chave}_proj`] = row && (row.selo === "modelado" || row.ano === ultimoNaoMod) ? v : null;
        linha[`${u.chave}_nivel`] = row ? row.nivel_fonte : null;
        linha._linhas[u.chave] = row;
      }
      return linha;
    });
  }, [anosFig1, unidadesFig1, modoFig1, porUnidade]); // eslint-disable-line react-hooks/exhaustive-deps

  const seloFig1 = useMemo(() => {
    let selo = null;
    for (const u of unidadesFig1) for (const r of linhasFig1De(u.chave)) if (!vazio(r.valor)) selo = piorSelo(selo, r.selo);
    return selo;
  }, [unidadesFig1, modoFig1, porUnidade]); // eslint-disable-line react-hooks/exhaustive-deps

  const unidadeMedidaFig1 = useMemo(() => {
    const rows = unidadesFig1.flatMap((u) => linhasFig1De(u.chave));
    return nomeUnidadeMedida(unidadesDe(rows));
  }, [unidadesFig1, modoFig1, porUnidade, lang]); // eslint-disable-line react-hooks/exhaustive-deps

  const subtituloFig1 = preencher(
    modoFig1 === "indice" ? T.fig1_subtitulo_indice : unidadeChave === "provincia" ? T.fig1_subtitulo_provincia : T.fig1_subtitulo_absoluto,
    { unidade: unidadeMedidaFig1 }
  );

  const listaBasesIndice = todasUnidades
    .filter((u) => porUnidade[u.chave]?.baseIndice)
    .map((u) => preencher(T.fig1_base_item, { unidade: T[u.rotuloId], ano: porUnidade[u.chave].baseIndice }))
    .join("; ");
  const anoVila = porUnidade.moatize_vila?.pop.find((r) => !vazio(r.valor))?.ano ?? "—";

  const tabelaFig1 = {
    legenda: T.ver_tabela_legenda_fig1,
    colunas: [
      { id: "unidade", rotulo: T.fig3_col_unidade },
      { id: "ano", rotulo: t("ano") },
      {
        id: "populacao",
        rotulo: `${T.tab_col_populacao} (${nomeUnidadeMedida(unidadesDe(todasUnidades.flatMap((u) => porUnidade[u.chave]?.pop ?? [])))})`,
        num: true,
        fmt: (l) => <CelulaProv linha={l.pop} formatador={fmtInt} />,
      },
      {
        id: "indice",
        rotulo: `${T.tab_col_indice} (${nomeUnidadeMedida(unidadesDe(todasUnidades.flatMap((u) => porUnidade[u.chave]?.indice ?? [])))})`,
        num: true,
        fmt: (l) => <CelulaProv linha={l.idx} formatador={fmtNum2} />,
      },
      { id: "selo", rotulo: t("selo"), fmt: (l) => (l.pop ? T.selo_rotulos[l.pop.selo] ?? l.pop.selo : T.tab_sem_linha) },
      { id: "nivel", rotulo: t("nivel"), fmt: (l) => (l.pop?.nivel_fonte ? `${T.nivel_rotulo_prefixo} ${l.pop.nivel_fonte}` : "—") },
    ],
    linhas: todasUnidades.flatMap((u) =>
      anosFig1.map((ano) => ({
        unidade: T[u.rotuloId],
        ano,
        pop: porUnidade[u.chave]?.pop.find((r) => r.ano === ano) ?? null,
        idx: porUnidade[u.chave]?.indice.find((r) => r.ano === ano) ?? null,
      }))
    ),
  };

  const linhaDoPontoFig1 = (dataKey, ponto) => ponto?._linhas?.[String(dataKey).replace(/_(solido|proj)$/, "")] ?? null;
  const linhaDoPonto = (dataKey, ponto) => ponto?._linhas?.[dataKey] ?? null;

  // --- Figura 2a: preço do carvão ---------------------------------------------------
  const dadosPreco = useMemo(() => {
    if (!preco) return [];
    const anos = [...new Set(preco.map((r) => r.ano))].filter((a) => typeof a === "number").sort((a, b) => a - b);
    return anos.map((ano) => {
      const au = preco.find((r) => r.ano === ano && r.variavel === "preco_carvao_australia") ?? null;
      const sa = preco.find((r) => r.ano === ano && r.variavel === "preco_carvao_africa_do_sul") ?? null;
      return {
        ano,
        australia: au && !vazio(au.valor) ? au.valor : null,
        africa_do_sul: sa && !vazio(sa.valor) ? sa.valor : null,
        _linhas: { australia: au, africa_do_sul: sa },
      };
    });
  }, [preco]);
  const unidadePreco = useMemo(() => unidadesDe(preco), [preco]);

  // --- Figura 2b: produção — estado vazio honesto até haver valor numérico ----------
  const producaoNumerica = useMemo(() => (producao ?? []).filter((r) => typeof r.valor === "number" && !vazio(r.valor)), [producao]);
  // Linhas "não disponível" agrupadas por (mina, motivo): o motivo não se repete por variável.
  const producaoAusente = useMemo(() => {
    const grupos = new Map();
    for (const r of producao ?? []) {
      if (typeof r.valor === "number") continue;
      const chave = `${r.unidade_geografica}__${r.nota}`;
      if (!grupos.has(chave)) grupos.set(chave, { unidade: r.unidade_geografica, row: r, variaveis: [] });
      const g = grupos.get(chave);
      if (r.variavel && !g.variaveis.includes(r.variavel)) g.variaveis.push(r.variavel);
    }
    return [...grupos.values()];
  }, [producao]);
  const seriesProducao = useMemo(() => {
    const vistas = new Map();
    for (const r of producaoNumerica) {
      const chave = `${r.unidade_geografica}|${r.variavel}`;
      if (!vistas.has(chave)) vistas.set(chave, { chave, unidade: r.unidade_geografica, variavel: r.variavel });
    }
    return [...vistas.values()];
  }, [producaoNumerica]);
  const dadosProducao = useMemo(() => {
    if (!producaoNumerica.length) return [];
    const anos = [...new Set(producaoNumerica.map((r) => r.ano))].sort((a, b) => a - b);
    // Uma série por (mina, variável): o CSV tem metalúrgico e térmico por ano e mina.
    // Chavear só pela mina pegava a primeira linha do ano e descartava o térmico.
    return anos.map((ano) => {
      const linha = { ano, _linhas: {} };
      for (const { chave, unidade, variavel } of seriesProducao) {
        const row = producaoNumerica.find((r) => r.ano === ano && r.unidade_geografica === unidade && r.variavel === variavel) ?? null;
        linha[chave] = row ? row.valor : null;
        linha._linhas[chave] = row;
      }
      return linha;
    });
  }, [producaoNumerica, seriesProducao]);
  const unidadeProducao = useMemo(() => unidadesDe(producaoNumerica), [producaoNumerica]);

  // --- Figura 2c: luz noturna -------------------------------------------------------
  const unidadesLuz = useMemo(() => {
    if (!luzes) return [];
    const todas = [...new Set(luzes.map((r) => r.unidade))].filter((u) => u && u !== "unidade");
    return luzComparacao === "so_tete" ? todas.filter((u) => u === "tete_aoi") : todas;
  }, [luzes, luzComparacao]);
  const dadosLuz = useMemo(() => {
    if (!luzes) return [];
    const anos = [...new Set(luzes.map((r) => r.ano))].filter((a) => typeof a === "number").sort((a, b) => a - b);
    return anos.map((ano) => {
      const linha = { ano, _linhas: {} };
      for (const u of unidadesLuz) {
        const row = luzes.find((r) => r.unidade === u && r.ano === ano) ?? null;
        linha[u] = row && !vazio(row.soma_radiancia) ? row.soma_radiancia : null;
        linha._linhas[u] = row;
      }
      return linha;
    });
  }, [luzes, unidadesLuz]);

  const metodoLuz = (row) => T.luz_metodo_linha.replace("{geometria}", row?.geometria ?? "—");
  const notaLuz = (row) =>
    row && !vazio(row.janela_homogenea)
      ? String(row.janela_homogenea).toLowerCase() === "true"
        ? T.luz_nota_janela_dentro
        : T.luz_nota_janela_fora
      : null;

  // Selo e nível da Figura 2 inteira: pior entre as linhas plotadas nos três painéis.
  const linhasPlotadasFig2 = useMemo(
    () => [
      ...(preco ?? []).filter((r) => !vazio(r.valor)),
      ...producaoNumerica,
      ...(luzes ?? []).filter((r) => unidadesLuz.includes(r.unidade) && !vazio(r.soma_radiancia)),
    ],
    [preco, producaoNumerica, luzes, unidadesLuz]
  );
  const seloFig2 = linhasPlotadasFig2.reduce((s, r) => piorSelo(s, r.selo), null);
  const nivelFig2 = linhasPlotadasFig2.reduce((s, r) => piorNivel(s, r.nivel_fonte), null);

  // Domínio X comum aos três painéis = anos cobertos pelos dados de preço e luz.
  const dominioAnos = useMemo(() => {
    const anos = [...dadosPreco, ...dadosLuz, ...dadosProducao].map((d) => d.ano).filter((a) => typeof a === "number");
    return anos.length ? [Math.min(...anos), Math.max(...anos)] : [0, 1];
  }, [dadosPreco, dadosLuz, dadosProducao]);
  const ticksAnos = anosTicks(dominioAnos);

  const fasesVisiveis = fases.filter((f) => f.ano_fim > dominioAnos[0] && f.ano_inicio < dominioAnos[1]);
  const marcosFig2 = pontuais.filter(
    (m) => TIPOS_MARCO_FIG2.includes(m.tipo) && m.ano_inicio >= dominioAnos[0] && m.ano_inicio <= dominioAnos[1]
  );
  const rotulosFasesNoPainel = larguraPaineis >= 720;

  const rendMarcos = (comRotulo) => (
    <>
      {fasesVisiveis.map((f, i) => (
        <ReferenceArea
          key={f.id}
          x1={Math.max(f.ano_inicio, dominioAnos[0])}
          x2={Math.min(f.ano_fim, dominioAnos[1])}
          fill={i % 2 === 0 ? "var(--ard-primaria-nevoa)" : "var(--ard-surface)"}
          fillOpacity={i % 2 === 0 ? 0.9 : 0}
          stroke="none"
          ifOverflow="hidden"
          label={
            comRotulo && rotulosFasesNoPainel
              ? { value: f.rotulo, position: "top", fontSize: 10, fill: "var(--ard-text-2)" }
              : undefined
          }
        />
      ))}
      {marcosFig2.map((m) => (
        <ReferenceLine key={m.id} x={m.ano_inicio} stroke="var(--ard-text-3)" strokeWidth={1} strokeOpacity={0.8} ifOverflow="hidden" />
      ))}
    </>
  );

  const eixoX = (
    <XAxis dataKey="ano" type="number" domain={dominioAnos} ticks={ticksAnos} allowDataOverflow tick={{ fontSize: 11 }} />
  );
  const grade = <CartesianGrid strokeDasharray="3 3" stroke="var(--ard-filete-cl)" vertical={false} />;

  const anosTabelaFig2 = [...new Set([...dadosPreco, ...dadosLuz].map((d) => d.ano))].sort((a, b) => a - b);
  const tabelaFig2 = {
    legenda: T.ver_tabela_legenda_fig2,
    colunas: [
      { id: "ano", rotulo: t("ano") },
      {
        id: "australia",
        rotulo: `${T.preco_australia} (${unidadePreco})`,
        num: true,
        fmt: (l) => <CelulaProv linha={l.p?._linhas.australia} valor={l.p?.australia} formatador={fmtNum2} />,
      },
      {
        id: "africa_do_sul",
        rotulo: `${T.preco_africa_do_sul} (${unidadePreco})`,
        num: true,
        fmt: (l) => <CelulaProv linha={l.p?._linhas.africa_do_sul} valor={l.p?.africa_do_sul} formatador={fmtNum2} />,
      },
      ...unidadesLuz.map((u) => ({
        id: u,
        rotulo: `${unidadeLuz(u, lang)} (${T.luz_unidade_nao_declarada})`,
        num: true,
        fmt: (l) => (
          <CelulaProv linha={l.l?._linhas[u]} valor={l.l?.[u]} formatador={fmtNum2} metodo={metodoLuz(l.l?._linhas[u])} nota={notaLuz(l.l?._linhas[u])} />
        ),
      })),
    ],
    linhas: anosTabelaFig2.map((ano) => ({
      ano,
      p: dadosPreco.find((d) => d.ano === ano) ?? null,
      l: dadosLuz.find((d) => d.ano === ano) ?? null,
    })),
  };

  if (erro) return <Erro erro={erro} />;
  if (carregando) return <Esqueleto altura={480} />;

  const alturaPainel = larguraPaineis && larguraPaineis < 520 ? 150 : 180;
  const corAtual = COR_UNIDADE[unidadeAtual.chave];

  return (
    <div className="provincia-pagina">
      <Secao kicker={T.kicker} titulo={T.titulo}>
        <p className="provincia-lead">{T.lead}</p>
      </Secao>

      <Segmentado
        rotulo={T.segmentado_unidade_rotulo}
        valor={unidadeChave}
        onChange={setUnidadeChave}
        opcoes={UNIDADES_CASCATA.map((u) => ({ valor: u.chave, rotulo: T[u.rotuloId] }))}
      />

      {kpis && (
        <div className="provincia-kpis">
          <Kpi
            rotulo={T.kpi_ultimo_censo_rotulo}
            valor={kpis.ultimoCenso ? <CelulaProv linha={kpis.ultimoCenso} formatador={fmtInt} unidadeMedida={nomeUnidadeMedida(kpis.ultimoCenso.unidade_medida)} /> : "—"}
            nota={
              unidadeAtual.chave === "moatize_vila"
                ? T.kpi_ultimo_censo_nota_vila
                : preencher(T.kpi_ultimo_censo_nota_padrao, { ano: kpis.ultimoCenso?.ano ?? "—" })
            }
          />
          <Kpi
            rotulo={kpis.projecao ? preencher(T.kpi_projecao_rotulo, { ano: kpis.projecao.ano }) : T.kpi_projecao_rotulo_sem_ano}
            valor={kpis.projecao ? <CelulaProv linha={kpis.projecao} formatador={fmtInt} unidadeMedida={nomeUnidadeMedida(kpis.projecao.unidade_medida)} /> : "—"}
            nota={kpis.projecao ? preencher(T.kpi_projecao_nota, { ano: kpis.projecao.ano }) : T.kpi_projecao_indisponivel}
          />
          {kpis.cagrs.length ? (
            kpis.cagrs.map(({ intervalo, row }) => (
              <Kpi
                key={intervalo}
                rotulo={preencher(T.kpi_cagr_rotulo_intervalo, { intervalo })}
                valor={<CelulaProv linha={row} formatador={fmtNum2} unidadeMedida={nomeUnidadeMedida(row.unidade_medida)} />}
              />
            ))
          ) : (
            <Kpi
              rotulo={T.kpi_cagr_rotulo_sem_intervalo}
              valor="—"
              nota={unidadeAtual.chave === "moatize_vila" ? preencher(T.kpi_cagr_vila_nota, { ano: anoVila }) : T.kpi_cagr_sem_dado}
            />
          )}
          <div className="ard-card">
            <p className="ard-kpi-label">{T.kpi_mini_serie_rotulo}</p>
            <div className="provincia-mini-serie">
              <MiniSerie pontos={kpis.serie} cor={corAtual} />
            </div>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------ Figura 1 */}
      <Figura
        kicker={T.kicker}
        titulo={preencher(T.fig1_titulo, { inicio: anosFig1[0] ?? "—", fim: anosFig1[anosFig1.length - 1] ?? "—" })}
        subtitulo={subtituloFig1}
        controles={
          <Segmentado
            rotulo={T.fig1_modo_rotulo}
            valor={modoFig1}
            onChange={setModoFig1}
            opcoes={[
              { valor: "absoluto", rotulo: T.fig1_modo_absoluto },
              { valor: "indice", rotulo: T.fig1_modo_indice },
            ]}
          />
        }
        fonte={T.fig1_fonte}
        metodo={T.fig1_metodo}
        selo={seloFig1 ? T.selo_rotulos[seloFig1] ?? seloFig1 : null}
        notas={
          <>
            {modoFig1 === "indice" && listaBasesIndice ? (
              <p className="provincia-nota-miuda">{preencher(T.fig1_base_indice, { lista: listaBasesIndice })}</p>
            ) : null}
            {unidadesFig1.some((u) => u.chave === "moatize_vila") ? (
              <p className="provincia-nota-miuda">{preencher(T.fig1_nota_moatize_vila, { ano: anoVila })}</p>
            ) : null}
          </>
        }
        tabela={tabelaFig1}
        altura={340}
      >
        <LineChart data={dadosFig1} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--ard-filete-cl)" />
          <XAxis dataKey="ano" type="number" domain={[anosFig1[0], anosFig1[anosFig1.length - 1]]} ticks={anosFig1} tick={{ fontSize: 11 }} padding={{ left: 14, right: 14 }} />
          <YAxis
            width={modoFig1 === "indice" ? 48 : 60}
            tickFormatter={modoFig1 === "indice" ? fmtInt : fmtCompacto}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            content={(props) => (
              <TooltipProv {...props} linhaDe={linhaDoPontoFig1} formatador={modoFig1 === "indice" ? fmtNum2 : fmtInt} unidade={null} T={T} t={t} />
            )}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {censos
            .map((c) => ({ id: c.id, ano: Number(String(c.inicio).slice(0, 4)) }))
            .filter((c) => anosFig1.includes(c.ano))
            .map((c) => (
              <ReferenceLine key={c.id} x={c.ano} stroke="var(--ard-text-3)" strokeDasharray="2 3" />
            ))}
          {unidadesFig1.map((u) => {
            const destaque = u.chave === unidadeChave;
            const cor = COR_UNIDADE[u.chave];
            return [
              <Line
                key={`${u.chave}-solido`}
                type="linear"
                dataKey={`${u.chave}_solido`}
                name={T[u.rotuloId]}
                stroke={cor}
                strokeWidth={destaque ? 3 : 1.5}
                strokeOpacity={destaque ? 1 : 0.85}
                dot={pontoPorNivel(`${u.chave}_nivel`, cor)}
                connectNulls
                isAnimationActive={false}
              />,
              <Line
                key={`${u.chave}-proj`}
                type="linear"
                dataKey={`${u.chave}_proj`}
                name={T[u.rotuloId]}
                stroke={cor}
                strokeWidth={destaque ? 3 : 1.5}
                strokeOpacity={destaque ? 1 : 0.85}
                strokeDasharray="5 4"
                dot={pontoPorNivel(`${u.chave}_nivel`, cor)}
                connectNulls
                legendType="none"
                isAnimationActive={false}
              />,
            ];
          })}
        </LineChart>
      </Figura>

      {/* ------------------------------------------------------------ Figura 2 */}
      <figure className="figura ard-card provincia-fig2" aria-labelledby={idFig2}>
        <header className="figura__cab">
          <p className="ard-kicker">{T.kicker}</p>
          <h3 id={idFig2} className="figura__titulo">
            {preencher(T.fig2_titulo, { inicio: dominioAnos[0], fim: dominioAnos[1] })}
          </h3>
          <p className="figura__sub">{T.fig2_subtitulo}</p>
          <div className="figura__controles">
            <Segmentado
              rotulo={T.fig2_luz_controle_rotulo}
              valor={luzComparacao}
              onChange={setLuzComparacao}
              opcoes={[
                { valor: "so_tete", rotulo: T.fig2_luz_controle_so_tete },
                { valor: "com_controles", rotulo: T.fig2_luz_controle_com_controles },
              ]}
            />
          </div>
        </header>

        <div className="figura__corpo" ref={refPaineis}>
          {verTabelaFig2 ? (
            <Tabela {...tabelaFig2} />
          ) : (
            <div className="provincia-paineis">
              {/* Painel a — preço */}
              <section className="provincia-painel" aria-label={T.fig2_painel_preco_titulo}>
                <h4 className="provincia-painel__titulo">
                  <span>
                    <span className="provincia-painel__letra">(a)</span> {T.fig2_painel_preco_titulo}{" "}
                    <span className="provincia-painel__unidade">{preencher(T.fig2_painel_unidade, { unidade: unidadePreco })}</span>
                  </span>
                  <LegendaHtml
                    itens={[
                      { rotulo: T.preco_australia, cor: CORES[0] },
                      { rotulo: T.preco_africa_do_sul, cor: CORES[1] },
                    ]}
                  />
                </h4>
                <ResponsiveContainer width="100%" height={alturaPainel}>
                  <LineChart data={dadosPreco} syncId="provincia-fig2" syncMethod="value" margin={rotulosFasesNoPainel ? MARGEM_PAINEL_TOPO : MARGEM_PAINEL}>
                    {rendMarcos(true)}
                    {grade}
                    {eixoX}
                    <YAxis width={LARG_EIXO_Y} tickFormatter={fmtInt} tick={{ fontSize: 11 }} />
                    <Tooltip content={(props) => <TooltipProv {...props} linhaDe={linhaDoPonto} formatador={fmtNum2} unidade={unidadePreco} T={T} t={t} />} />
                    <Line type="linear" dataKey="australia" name={T.preco_australia} stroke={CORES[0]} strokeWidth={2} dot={false} connectNulls isAnimationActive={false} />
                    <Line type="linear" dataKey="africa_do_sul" name={T.preco_africa_do_sul} stroke={CORES[1]} strokeWidth={2} dot={false} connectNulls isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </section>

              {/* Painel b — produção */}
              <section className="provincia-painel" aria-label={T.fig2_painel_producao_titulo}>
                <h4 className="provincia-painel__titulo">
                  <span>
                    <span className="provincia-painel__letra">(b)</span> {T.fig2_painel_producao_titulo}
                    {unidadeProducao ? (
                      <>
                        {" "}
                        <span className="provincia-painel__unidade">{preencher(T.fig2_painel_unidade, { unidade: unidadeProducao })}</span>
                      </>
                    ) : null}
                  </span>
                </h4>
                {/* Proveniência (com o motivo técnico) fora da caixa rolável, para o
                    tooltip não ser recortado pelo overflow dela. */}
                {!dadosProducao.length && producaoAusente.length ? (
                  <p className="provincia-painel__prov">
                    {T.fig2_producao_prov_rotulo}:{" "}
                    {producaoAusente.map((g, i) => (
                      <span key={`${g.unidade}-${g.row.nota}`}>
                        {i ? " · " : ""}
                        <ProvenanciaNumero
                          valor={g.unidade}
                          fonte={g.row.fonte}
                          metodo={g.row.metodo}
                          selo={g.row.selo}
                          nivelFonte={g.row.nivel_fonte}
                          nota={g.row.nota}
                        />
                      </span>
                    ))}
                  </p>
                ) : null}
                {dadosProducao.length ? (
                  <ResponsiveContainer width="100%" height={alturaPainel}>
                    <LineChart data={dadosProducao} syncId="provincia-fig2" syncMethod="value" margin={MARGEM_PAINEL}>
                      {rendMarcos(false)}
                      {grade}
                      {eixoX}
                      <YAxis width={LARG_EIXO_Y} tickFormatter={fmtCompacto} tick={{ fontSize: 11 }} />
                      <Tooltip content={(props) => <TooltipProv {...props} linhaDe={linhaDoPonto} formatador={fmtNum2} unidade={unidadeProducao} T={T} t={t} />} />
                      <Legend verticalAlign="top" align="right" height={24} wrapperStyle={{ fontSize: 12 }} />
                      {seriesProducao.map((sr, i) => {
                        const variasMinas = new Set(seriesProducao.map((x) => x.unidade)).size > 1;
                        const nome = variasMinas ? `${sr.unidade} — ${nomeVariavel(sr.variavel)}` : nomeVariavel(sr.variavel);
                        return (
                          <Line key={sr.chave} type="linear" dataKey={sr.chave} name={nome} stroke={CORES[i % CORES.length]} strokeWidth={2} dot connectNulls={false} isAnimationActive={false} />
                        );
                      })}
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="provincia-painel-vazio" role="note" style={{ height: alturaPainel, marginLeft: LARG_EIXO_Y, marginRight: MARGEM_PAINEL.right }}>
                    <p className="provincia-painel-vazio__frase">
                      {producaoAusente.every((g) => RE_MOTIVO_SEC.test(g.row.nota ?? "")) ? T.fig2_producao_vazio_frase : T.fig2_producao_vazio_frase_generica}
                    </p>
                    <div className="provincia-painel-vazio__grupos">
                    {producaoAusente.map((g) => (
                      <div key={`${g.unidade}-${g.row.nota}`} className="provincia-painel-vazio__grupo">
                        <p className="provincia-painel-vazio__mina">
                          <strong>{g.unidade}</strong>
                        </p>
                        <ul aria-label={T.fig2_producao_vazio_lista}>
                          {g.variaveis.map((v) => (
                            <li key={v}>{nomeVariavel(v)}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                    </div>
                  </div>
                )}
              </section>

              {/* Painel c — luz */}
              <section className="provincia-painel" aria-label={T.fig2_painel_luz_titulo}>
                <h4 className="provincia-painel__titulo">
                  <span>
                    <span className="provincia-painel__letra">(c)</span> {T.fig2_painel_luz_titulo}{" "}
                    <span className="provincia-painel__unidade">{preencher(T.fig2_painel_unidade, { unidade: T.luz_unidade_nao_declarada })}</span>
                  </span>
                  {unidadesLuz.length > 1 ? (
                    <LegendaHtml
                      itens={unidadesLuz.map((u, i) => ({ rotulo: unidadeLuz(u, lang), cor: u === "tete_aoi" ? CORES[0] : CORES[(i % (CORES.length - 1)) + 1] }))}
                    />
                  ) : null}
                </h4>
                <ResponsiveContainer width="100%" height={alturaPainel}>
                  <LineChart data={dadosLuz} syncId="provincia-fig2" syncMethod="value" margin={MARGEM_PAINEL}>
                    {rendMarcos(false)}
                    {grade}
                    {eixoX}
                    <YAxis width={LARG_EIXO_Y} tickFormatter={fmtCompacto} tick={{ fontSize: 11 }} />
                    <Tooltip content={(props) => <TooltipProv {...props} linhaDe={linhaDoPonto} formatador={fmtNum2} unidade={null} T={T} t={t} />} />
                    {unidadesLuz.map((u, i) => (
                      <Line
                        key={u}
                        type="linear"
                        dataKey={u}
                        name={unidadeLuz(u, lang)}
                        stroke={u === "tete_aoi" ? CORES[0] : CORES[(i % (CORES.length - 1)) + 1]}
                        strokeWidth={u === "tete_aoi" ? 2.5 : 1.4}
                        strokeDasharray={u === "tete_aoi" ? undefined : "4 3"}
                        dot={false}
                        connectNulls
                        isAnimationActive={false}
                      />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              </section>

              <div className="provincia-chave">
                <p>
                  <span className="rotulo-fonte">{T.fig2_legenda_fases}:</span>{" "}
                  {fasesVisiveis.map((f, i) => (
                    <span key={f.id} className="provincia-chave__fase">
                      <span aria-hidden="true" className={"provincia-chave__amostra" + (i % 2 === 0 ? " provincia-chave__amostra--sombra" : "")} />
                      {f.rotulo} ({f.inicio}–{f.fim})
                    </span>
                  ))}
                </p>
                <p>
                  <span className="rotulo-fonte">{T.fig2_legenda_marcos}:</span>{" "}
                  {marcosFig2.map((m, i) => (
                    <span key={m.id}>
                      {i ? " · " : ""}
                      {m.rotulo} ({m.inicio})
                    </span>
                  ))}
                </p>
              </div>
            </div>
          )}
        </div>

        <figcaption className="figura__rodape">
          <span className="figura__fonte">
            <span className="rotulo-fonte">{t("fonte")}:</span> {T.fig2_fonte} · <span className="rotulo-fonte">{t("metodo")}:</span> {T.fig2_metodo}
            {seloFig2 ? (
              <>
                {" "}
                · <span className="rotulo-fonte">{t("selo")}:</span> {T.selo_rotulos[seloFig2] ?? seloFig2}
              </>
            ) : null}
            {nivelFig2 ? (
              <>
                {" "}
                · <span className="rotulo-fonte">{t("nivel")}:</span> {nivelFig2}
              </>
            ) : null}
          </span>
          <button type="button" className="botao-texto" aria-pressed={verTabelaFig2} onClick={() => setVerTabelaFig2((v) => !v)}>
            {verTabelaFig2 ? t("ver_grafico") : t("ver_tabela")}
          </button>
        </figcaption>
        <div className="figura__notas">
          <p className="provincia-caixa-atencao">{interpolarComPartes(T.fig2_luz_aviso, { rotulo: unidadeLuz("tete_aoi", lang) })}</p>
          {!dadosProducao.length ? <p className="provincia-nota-miuda">{T.fig2_producao_vazio_rodape}</p> : null}
        </div>
      </figure>

      {/* ------------------------------------------------------------ Figura 3 */}
      <Secao kicker={T.kicker} titulo={T.fig3_titulo} />
      <div className="ard-card provincia-contas" aria-label={T.fig3_titulo}>
        <div className="provincia-caixa-atencao">{preencher(T.fig3_aviso, { n: (contas ?? []).length })}</div>
        <Tabela
          legenda={T.fig3_titulo}
          colunas={[
            { id: "unidade_geografica", rotulo: T.fig3_col_unidade, fmt: (l) => T.unidades_geo?.[l.unidade_geografica] ?? l.unidade_geografica },
            { id: "ano", rotulo: T.fig3_col_ano },
            { id: "variavel", rotulo: T.fig3_col_variavel, fmt: (l) => nomeVariavel(l.variavel) },
            {
              id: "valor",
              rotulo: T.fig3_col_valor,
              num: true,
              fmt: (l) => <CelulaProv linha={l} formatador={fmtNum2} unidadeMedida={nomeUnidadeMedida(l.unidade_medida)} />,
            },
          ]}
          linhas={contas ?? []}
        />
        <p className="provincia-nota-miuda">
          {t("fonte")}: {T.fig3_fonte}
        </p>
      </div>

      {/* ------------------------------------------------------------ Ausências */}
      <Secao kicker={T.kicker} titulo={T.bloco_ausencias_titulo}>
        <p className="provincia-lead">{T.bloco_ausencias_intro}</p>
      </Secao>
      <div className="ard-card provincia-ausencias">
        <table className="provincia-tabela-ausencias">
          <thead>
            <tr>
              <th>{T.bloco_ausencias_col_item}</th>
              <th>{T.bloco_ausencias_col_motivo}</th>
            </tr>
          </thead>
          <tbody>
            {(contexto ?? []).map((r, i) => (
              <tr key={`ctx-${i}`}>
                <td>
                  {r.unidade_geografica} · {r.ano} · {nomeVariavel(r.variavel)}
                </td>
                <td>{r.motivo_nao_nucleo}</td>
              </tr>
            ))}
            {producaoAusente.map((g) => (
              <tr key={`prod-${g.unidade}-${g.row.nota}`}>
                <td>
                  <strong>{g.unidade}</strong>
                  <ul className="provincia-lista-simples">
                    {g.variaveis.map((v) => (
                      <li key={v}>{nomeVariavel(v)}</li>
                    ))}
                  </ul>
                </td>
                <td>
                  {RE_MOTIVO_SEC.test(g.row.nota ?? "") ? T.fig2_producao_vazio_frase : g.row.nota}{" "}
                  <ProvenanciaNumero
                    valor={T.ausencias_prov_rotulo}
                    fonte={g.row.fonte}
                    metodo={g.row.metodo}
                    selo={g.row.selo}
                    nivelFonte={g.row.nivel_fonte}
                    nota={g.row.nota}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
