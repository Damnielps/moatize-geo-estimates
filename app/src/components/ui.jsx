// Componentes de interface do painel (Sistema Ardósia), portados de
// urban-canaa/web/src/components/ui.tsx (TS + ECharts) para JSX + Recharts, sem mudar
// a stack deste repositório. Figura com tabela alternativa, KPI com sparkline, tabela
// acessível, glossário com tooltip, seção, controle segmentado, esqueleto de carga e
// erro. Tokens só de app/src/ardosia.css — nenhum hex novo solto aqui.
import { useId, useState } from "react";
import { ResponsiveContainer } from "recharts";
import { useI18n } from "../lib/i18n.jsx";

const TRACO = "—";

// ---------------------------------------------------------------------------
// Figura: kicker + título serifado + gráfico (ResponsiveContainer) + fonte/método/selo
// + botão "Ver tabela" / "Ver gráfico" (acessibilidade — CLAUDE.md §6.6/§10)
// ---------------------------------------------------------------------------

export function Figura({
  kicker,
  titulo,
  subtitulo,
  fonte,
  metodo,
  selo,
  notas,
  /** Visão em tabela dos mesmos dados: { colunas, linhas, legenda }. */
  tabela,
  children,
  controles,
  className,
  /** Altura do ResponsiveContainer, em px — mesma usada pelo GraficoCard anterior. */
  altura = 320,
}) {
  const { t } = useI18n();
  const [verTabela, setVerTabela] = useState(false);
  const id = useId();
  return (
    <figure className={"figura ard-card " + (className ?? "")} aria-labelledby={id}>
      <header className="figura__cab">
        {kicker && <p className="ard-kicker">{kicker}</p>}
        <h3 id={id} className="figura__titulo">
          {titulo}
        </h3>
        {subtitulo && <p className="figura__sub">{subtitulo}</p>}
        {controles && <div className="figura__controles">{controles}</div>}
      </header>
      <div className="figura__corpo">
        {verTabela && tabela ? (
          <Tabela {...tabela} />
        ) : (
          <ResponsiveContainer width="100%" height={altura}>
            {children}
          </ResponsiveContainer>
        )}
      </div>
      <figcaption className="figura__rodape">
        <span className="figura__fonte">
          <span className="rotulo-fonte">{t("fonte")}:</span> {fonte}
          {metodo ? (
            <>
              {" "}
              · <span className="rotulo-fonte">{t("metodo")}:</span> {metodo}
            </>
          ) : null}
          {selo ? (
            <>
              {" "}
              · <span className="rotulo-fonte">{t("selo")}:</span> {selo}
            </>
          ) : null}
        </span>
        {tabela && (
          <button
            type="button"
            className="botao-texto"
            aria-pressed={verTabela}
            onClick={() => setVerTabela((v) => !v)}
          >
            {verTabela ? t("ver_grafico") : t("ver_tabela")}
          </button>
        )}
      </figcaption>
      {notas && <div className="figura__notas">{notas}</div>}
    </figure>
  );
}

// ---------------------------------------------------------------------------
// Tabela — alternativa acessível a um gráfico (colunas: [{id, rotulo, num?, fmt?}])
// ---------------------------------------------------------------------------

export function Tabela({ colunas, linhas, legenda }) {
  return (
    <div className="tabela-wrap" tabIndex={0} role="region" aria-label={legenda ?? "Tabela de dados"}>
      <table>
        {legenda && <caption className="sr-only">{legenda}</caption>}
        <thead>
          <tr>
            {colunas.map((c) => (
              <th key={c.id} className={c.num ? "num" : undefined} scope="col">
                {c.rotulo}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {linhas.map((l, i) => (
            <tr key={i}>
              {colunas.map((c) => {
                const v = c.fmt ? c.fmt(l) : l[c.id];
                return (
                  <td key={c.id} className={c.num ? "num" : undefined}>
                    {v === null || v === undefined || v === "" ? TRACO : v}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// KPI com delta e sparkline
// ---------------------------------------------------------------------------

export function Kpi({ rotulo, valor, unidade, delta, nota, serie, destaque }) {
  return (
    <div className="kpi ard-card">
      <p className="ard-kpi-label">{rotulo}</p>
      <p className="ard-kpi-value">
        {valor}
        {unidade && <span className="kpi__unidade"> {unidade}</span>}
      </p>
      {delta && <p className="kpi__delta">{delta}</p>}
      {serie && serie.length > 1 && <Sparkline serie={serie} destaque={destaque} />}
      {nota && <p className="kpi__nota">{nota}</p>}
    </div>
  );
}

export function Sparkline({ serie, destaque, altura = 28 }) {
  const w = 120;
  const vals = serie.filter((v) => v !== null && Number.isFinite(v));
  if (vals.length < 2) return null;
  const min = Math.min(...vals);
  const max = Math.max(...vals);
  const x = (i) => (i / (serie.length - 1)) * (w - 6) + 3;
  const y = (v) => altura - 3 - ((v - min) / (max - min || 1)) * (altura - 6);
  let d = "";
  serie.forEach((v, i) => {
    if (v === null || !Number.isFinite(v)) return;
    d += (d && serie[i - 1] !== null ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1);
  });
  const vd = destaque !== undefined ? serie[destaque] : null;
  return (
    <svg className="sparkline" viewBox={`0 0 ${w} ${altura}`} width={w} height={altura} aria-hidden="true">
      <path d={d} fill="none" stroke="var(--ard-primaria)" strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
      {vd !== null && vd !== undefined && destaque !== undefined && (
        <circle cx={x(destaque)} cy={y(vd)} r={3} fill="var(--ard-acento)" stroke="var(--ard-surface)" strokeWidth={1.5} />
      )}
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Glossário bilíngue e Termo (tooltip acessível sob clique/hover/foco)
// ---------------------------------------------------------------------------

export const GLOSSARIO = {
  pt: {
    mancha_urbana:
      "Mancha urbana: área construída contígua classificada ano a ano em imagens Landsat/Sentinel-2, com regras de área mínima e permanência (§5.1), fora dos polígonos de mineração e dos buffers de reassentamento.",
    pegada_industrial:
      "Pegada industrial/minerária: cavas, pilhas de estéril, planta de beneficiamento, pátio ferroviário e corredor logístico — camada mutuamente exclusiva da mancha urbana e do reassentamento (§5.1). Nenhuma cava de mina é contada como área urbana.",
    reassentamento:
      "Reassentamento: povoado ou bairro criado para receber famílias deslocadas por um projeto minerário (ex.: Cateme, 25 de Setembro, Mwaladzi). Camada distinta de crescimento orgânico e de pegada industrial — misturá-las é o erro metodológico central que este estudo evita (CLAUDE.md §0).",
    selo_observado:
      "Selo observado: valor lido diretamente de um censo, imagem classificada ou registro administrativo, sem interpolação nem modelo.",
    selo_interpolado:
      "Selo interpolado: valor calculado entre dois pontos observados (ex.: geometricamente entre dois censos), sem nova observação no ano em questão.",
    selo_modelado:
      "Selo modelado: valor produzido por um modelo ou projeção (ex.: GHSL 2025/2030, projeção institucional do INE) — não é uma recontagem nem uma observação direta.",
    nivel_fonte:
      "Nível de fonte (§4.0): A = aberto, sustenta números publicados; B = livre com restrição, só validação; C = fechado ou incerto, proibido. Sem licença localizável, a fonte é C por definição.",
    churn:
      "Churn (instabilidade): mudança de classificação de um mesmo pixel entre dois anos-âncora que não corresponde a uma transição real no terreno — ruído do método de classificação, não um evento a interpretar.",
  },
  en: {
    mancha_urbana:
      "Urban footprint: contiguous built-up area classified year by year from Landsat/Sentinel-2 imagery, with minimum-area and persistence rules (§5.1), outside mining polygons and resettlement buffers.",
    pegada_industrial:
      "Industrial/mining footprint: pits, waste-rock piles, processing plant, rail yard and logistics corridor — a layer mutually exclusive with the urban footprint and resettlement (§5.1). No mine pit is ever counted as urban area.",
    reassentamento:
      "Resettlement: a village or neighbourhood created to receive families displaced by a mining project (e.g. Cateme, 25 de Setembro, Mwaladzi). A layer distinct from organic growth and from the industrial footprint — mixing them is the central methodological error this study avoids (CLAUDE.md §0).",
    selo_observado:
      "Observed stamp: value read directly from a census, a classified image, or an administrative record, with no interpolation or model.",
    selo_interpolado:
      "Interpolated stamp: value computed between two observed points (e.g. geometrically between two censuses), with no new observation in the year in question.",
    selo_modelado:
      "Modeled stamp: value produced by a model or projection (e.g. GHSL 2025/2030, an INE institutional projection) — not a recount nor a direct observation.",
    nivel_fonte:
      "Source level (§4.0): A = open, supports published numbers; B = free with restrictions, validation only; C = closed or uncertain, forbidden. Without a locatable licence, the source is C by definition.",
    churn:
      "Churn (instability): a change in the classification of the same pixel between two anchor years that does not correspond to a real change on the ground — noise from the classification method, not an event to interpret.",
  },
};

export function Termo({ id, children }) {
  const { lang } = useI18n();
  const [aberto, setAberto] = useState(false);
  const tid = useId();
  const def = GLOSSARIO[lang]?.[id] ?? GLOSSARIO.pt[id];
  if (!def) return <>{children}</>;
  return (
    <span className="termo">
      <button
        type="button"
        className="termo__botao"
        aria-describedby={aberto ? tid : undefined}
        aria-expanded={aberto}
        onClick={() => setAberto((a) => !a)}
        onBlur={() => setAberto(false)}
        onMouseEnter={() => setAberto(true)}
        onMouseLeave={() => setAberto(false)}
      >
        {children}
      </button>
      {aberto && (
        <span role="tooltip" id={tid} className="termo__def">
          {def}
        </span>
      )}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Seção de página: kicker + título + introdução em coluna de leitura
// ---------------------------------------------------------------------------

export function Secao({ kicker, titulo, children, id }) {
  return (
    <section className="secao" id={id} aria-labelledby={id ? id + "-t" : undefined}>
      <p className="ard-kicker">{kicker}</p>
      <h2 id={id ? id + "-t" : undefined}>{titulo}</h2>
      {children && <div className="secao__intro">{children}</div>}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Controle segmentado — radiogroup navegável por setas (acessibilidade §6.7)
// ---------------------------------------------------------------------------

export function Segmentado({ rotulo, opcoes, valor, onChange }) {
  function aoTeclar(e, indice) {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const habilitadas = opcoes.filter((o) => !o.desabilitado);
    if (!habilitadas.length) return;
    const atual = habilitadas.findIndex((o) => o.valor === valor);
    const passo = e.key === "ArrowRight" ? 1 : -1;
    const proximo = habilitadas[(((atual < 0 ? 0 : atual) + passo) % habilitadas.length + habilitadas.length) % habilitadas.length];
    onChange(proximo.valor);
  }
  return (
    <div className="segmentado" role="radiogroup" aria-label={rotulo}>
      <span className="segmentado__rotulo">{rotulo}</span>
      {opcoes.map((o, i) => (
        <button
          key={String(o.valor)}
          type="button"
          role="radio"
          aria-checked={o.valor === valor}
          disabled={o.desabilitado}
          className={"segmentado__op" + (o.valor === valor ? " ativo" : "")}
          onClick={() => onChange(o.valor)}
          onKeyDown={(e) => aoTeclar(e, i)}
        >
          {o.rotulo}
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Estados de carga
// ---------------------------------------------------------------------------

export function Esqueleto({ altura = 240 }) {
  return <div className="esqueleto" style={{ height: altura }} aria-busy="true" aria-label="Carregando" />;
}

export function Erro({ erro }) {
  const { lang } = useI18n();
  const msg = erro?.message ?? String(erro ?? "");
  return (
    <p className="erro" role="alert">
      {lang === "pt" ? `Não foi possível carregar os dados (${msg}).` : `Could not load the data (${msg}).`}
    </p>
  );
}
