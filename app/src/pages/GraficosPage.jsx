import { useEffect, useMemo, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  BarChart, Bar,
} from "recharts";
import { carregarCsv } from "../lib/data.js";
import { unidadeLuz } from "../lib/series.js";
import { useI18n } from "../lib/i18n.jsx";
import { formatarNumero } from "../lib/formato.js";
import VeredictoCausal from "../components/VeredictoCausal.jsx";
import { Figura } from "../components/ui.jsx";

const CORES = ["#24404F", "#9C5B41", "#3D5A4C", "#7E9BAA", "#A98A3F", "#6E3B45"];

export default function GraficosPage() {
  const { t, lang } = useI18n();
  // Eixos e tooltips do Recharts pelo idioma (PT vírgula decimal) — o padrão do Recharts
  // imprime o número cru, com ponto.
  const fmtEixo = (v) => (typeof v === "number" ? formatarNumero(v, lang, { max: 1 }) : v);
  const fmtTooltip = (v) => (typeof v === "number" ? formatarNumero(v, lang, { max: 2 }) : v);
  const [stats, setStats] = useState([]);
  const [luzes, setLuzes] = useState([]);

  useEffect(() => {
    carregarCsv("csv/stats_by_year_by_unit.csv").then(setStats);
    carregarCsv("causal/serie_luzes_anual.csv").then(setLuzes);
  }, []);

  // --- 1. Índice 2000 = 100: área urbana (tete) e luzes noturnas (tete_aoi) ---
  const areaTete = useMemo(
    () =>
      stats
        .filter((r) => r.unidade_geografica === "tete" && r.familia === "forma_urbana" && r.variavel === "area_km2_urbano")
        .sort((a, b) => a.ano - b.ano),
    [stats]
  );
  const luzTete = useMemo(
    () =>
      luzes
        .filter((r) => r.unidade === "tete_aoi" && [2000, 2005, 2010, 2015, 2020, 2025].includes(r.ano))
        .sort((a, b) => a.ano - b.ano),
    [luzes]
  );
  const indiceDados = useMemo(() => {
    if (!areaTete.length || !luzTete.length) return [];
    const baseArea = areaTete[0].valor;
    const baseLuz = luzTete[0].soma_radiancia;
    return areaTete.map((r, i) => ({
      ano: r.ano,
      area_urbana: (r.valor / baseArea) * 100,
      luz_noturna: luzTete[i] ? (luzTete[i].soma_radiancia / baseLuz) * 100 : null,
    }));
  }, [areaTete, luzTete]);

  // --- 2. Rosa de expansão (16 setores; intervalo DESCOBERTO do dado) ---
  //
  // Defeito corrigido (ORCHESTRATION_LOG.md 4-15): esta rosa fixava
  // `ano === 2025` e `desde_2000`, combinação que **não existe** no CSV. Cada ano-âncora
  // nomeia a variável pelo âncora ANTERIOR (2025 traz `desde_2020`), de modo que a busca
  // nunca casava e o gráfico ficava em branco — sem erro, porque `find` devolve
  // `undefined` e o componente renderizava um array vazio.
  //
  // Agora o par (ano, base) é derivado do próprio dado e o título declara o intervalo
  // REAL. Rotular "2000→2025" um dado que mede 2020→2025 seria a mesma classe de erro
  // relacional que reprovou a Fase 4 oito vezes: número certo, período errado.
  const rosaInfo = useMemo(() => {
    const re = /^frac_novo_setor_(\d{2})_desde_(\d{4})$/;
    const pares = stats
      .filter((r) => r.unidade_geografica === "tete" && re.test(String(r.variavel)))
      .map((r) => ({ ano: r.ano, base: Number(String(r.variavel).match(re)[2]) }));
    if (!pares.length) return null;
    const maisRecente = pares.reduce((a, b) => (b.ano > a.ano ? b : a));
    return { ano: maisRecente.ano, base: maisRecente.base };
  }, [stats]);

  const rosaDados = useMemo(() => {
    if (!rosaInfo) return [];
    return Array.from({ length: 16 }, (_, i) => {
      const codigo = String(i).padStart(2, "0");
      const row = stats.find(
        (r) =>
          r.unidade_geografica === "tete" &&
          r.ano === rosaInfo.ano &&
          r.variavel === `frac_novo_setor_${codigo}_desde_${rosaInfo.base}`
      );
      return { setor: `${i * 22.5}°`, fracao: row ? row.valor * 100 : 0 };
    });
  }, [stats, rosaInfo]);

  // --- 3. Barras empilhadas por tipologia (infill/borda/leapfrog) por período ---
  const periodos = [2000, 2005, 2010, 2015, 2020];
  const tipologiaDados = useMemo(
    () =>
      periodos.map((p) => {
        // Cada período é gravado no âncora SEGUINTE (`desde_2000` está em ano 2005, …,
        // `desde_2020` em 2025). Buscar tudo em 2025 deixava só a última barra preenchida.
        const fim = p + 5;
        const linha = (variavel) => stats.find((r) => r.unidade_geografica === "tete" && r.ano === fim && r.variavel === `${variavel}_desde_${p}`);
        const infill = linha("prop_infill")?.valor ?? null;
        const borda = linha("prop_borda")?.valor ?? null;
        const leapfrog = linha("prop_leapfrog")?.valor ?? null;
        return {
          periodo: `${p}→${fim}`,
          infill: infill != null ? infill * 100 : null,
          borda: borda != null ? borda * 100 : null,
          leapfrog: leapfrog != null ? leapfrog * 100 : null,
        };
      }),
    [stats]
  );

  // --- 4. Comparação com cidades-controle: luz noturna indexada a 2000 = 100 ---
  const cidadesControle = useMemo(() => {
    const unidades = [...new Set(luzes.map((r) => r.unidade))];
    return unidades.map((u) => {
      const serie = luzes
        .filter((r) => r.unidade === u && [2000, 2005, 2010, 2015, 2020, 2025].includes(r.ano))
        .sort((a, b) => a.ano - b.ano);
      const base = serie[0]?.soma_radiancia;
      return { unidade: u, papel: serie[0]?.papel, serie: serie.map((r) => ({ ano: r.ano, valor: base ? (r.soma_radiancia / base) * 100 : null })) };
    });
  }, [luzes]);
  const comparacaoDados = useMemo(() => {
    const anos = [2000, 2005, 2010, 2015, 2020, 2025];
    return anos.map((ano) => {
      const linha = { ano };
      cidadesControle.forEach((c) => {
        const ponto = c.serie.find((s) => s.ano === ano);
        linha[c.unidade] = ponto ? ponto.valor : null;
      });
      return linha;
    });
  }, [cidadesControle]);

  return (
    <div>
      <h2>{t("nav_graficos")}</h2>

      <Figura
        titulo="Índice 2000 = 100 — área urbana × luz noturna"
        fonte="area_km2_urbano (forma_urbana, unidade tete) · soma_radiancia (causal/serie_luzes_anual.csv, tete_aoi)"
        metodo="Razão simples ao valor de 2000, ×100. Área urbana é catraca não-decrescente por construção (ADR 0013); NÃO inclui população por falta de âncora censitária antes de 2017 para esta unidade."
        selo="observado (área com R1/R2) / observado (luz VIIRS harmonizada)"
      >
        <LineChart data={indiceDados}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--ard-filete-cl)" />
          <XAxis dataKey="ano" />
          <YAxis tickFormatter={fmtEixo} />
          <Tooltip formatter={fmtTooltip} />
          <Legend />
          <Line type="linear" dataKey="area_urbana" name="área urbana" stroke={CORES[0]} strokeWidth={2} dot />
          <Line type="linear" dataKey="luz_noturna" name="luz noturna (soma radiância)" stroke={CORES[1]} strokeWidth={2} dot />
        </LineChart>
      </Figura>

      <Figura
        titulo={`Rosa de expansão — Tete, ${rosaInfo ? `${rosaInfo.base}→${rosaInfo.ano}` : "intervalo indisponível"} (16 setores de 22,5°)`}
        fonte={`stats_by_year_by_unit.csv, familia forma_urbana, variável frac_novo_setor_NN_desde_${rosaInfo ? rosaInfo.base : "?"}, unidade tete, ano ${rosaInfo ? rosaInfo.ano : "?"}`}
        metodo={`Fração da área nova (${rosaInfo ? `${rosaInfo.base}→${rosaInfo.ano}` : "—"}) em cada setor direcional de 22,5° a partir do centroide da mancha de ${rosaInfo ? rosaInfo.base : "—"}. Cada ano-âncora mede o intervalo desde o âncora anterior, não desde 2000.`}
        selo="observado"
      >
        <RadarChart data={rosaDados} outerRadius={110}>
          <PolarGrid stroke="var(--ard-filete-cl)" />
          <PolarAngleAxis dataKey="setor" />
          <PolarRadiusAxis angle={30} tickFormatter={fmtEixo} />
          <Radar name="% da expansão" dataKey="fracao" stroke={CORES[0]} fill={CORES[0]} fillOpacity={0.4} />
          <Tooltip formatter={fmtTooltip} />
        </RadarChart>
      </Figura>

      <Figura
        titulo="Tipologia de expansão por período (infill / borda / leapfrog)"
        fonte="stats_by_year_by_unit.csv, variáveis prop_infill/prop_borda/prop_leapfrog_desde_YYYY, unidade tete, cada período lido no ano-âncora em que termina"
        metodo="Proporção da área nova classificada por adjacência à mancha existente no início do período. Herda o churn de classificação entre anos-âncora (ADR 0013) — não é medida livre de ruído."
        selo="observado, EXPERIMENTAL (herda churn)"
      >
        <BarChart data={tipologiaDados}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--ard-filete-cl)" />
          <XAxis dataKey="periodo" />
          <YAxis unit="%" tickFormatter={fmtEixo} domain={[0, 100]} ticks={[0, 25, 50, 75, 100]} allowDataOverflow />
          <Tooltip formatter={fmtTooltip} />
          <Legend />
          <Bar dataKey="infill" stackId="a" name="infill" fill={CORES[0]} />
          <Bar dataKey="borda" stackId="a" name="borda" fill={CORES[1]} />
          <Bar dataKey="leapfrog" stackId="a" name="leapfrog" fill={CORES[4]} />
        </BarChart>
      </Figura>

      <Figura
        titulo="Comparação com cidades-controle — luz noturna indexada (2000 = 100)"
        fonte="data/processed/causal/serie_luzes_anual.csv (Chen, Yu et al. 2021, ESSD, harmonizado DMSP-VIIRS)"
        metodo="Cada cidade indexada ao seu próprio valor de 2000 = 100. Tete (tratada) vs. Chimoio, Quelimane, Lichinga, Xai-Xai, Inhambane (controles, §3). Comparação NÃO sustenta inferência causal (veredito_fase3.csv: contrafactual não sustentado nas 4 quebras testadas)."
        selo="observado"
      >
        <LineChart data={comparacaoDados}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--ard-filete-cl)" />
          {/* Eixo numérico com os anos-âncora como ticks: cada linha usa os dados do
              LineChart — passar `data` também em cada <Line> fazia o Recharts repetir as
              categorias por série (2000…2025 uma vez por cidade). */}
          <XAxis dataKey="ano" type="number" domain={[2000, 2025]} ticks={[2000, 2005, 2010, 2015, 2020, 2025]} allowDecimals={false} />
          <YAxis tickFormatter={fmtEixo} />
          <Tooltip formatter={fmtTooltip} labelFormatter={(a) => String(a)} />
          <Legend />
          {cidadesControle.map((c, i) => (
            <Line
              key={c.unidade}
              // Segmentos retos entre anos-âncora observados: a curva suavizada sugeria
              // valores intermediários que a série não tem (mesmo espírito do ADR 0013).
              type="linear"
              dataKey={c.unidade}
              name={
                c.papel === "tratada"
                  ? unidadeLuz(c.unidade, lang).replace(/\)$/, lang === "en" ? ", treated)" : ", tratada)")
                  : unidadeLuz(c.unidade, lang)
              }
              stroke={CORES[i % CORES.length]}
              strokeWidth={c.papel === "tratada" ? 3 : 1.5}
              dot={{ r: c.papel === "tratada" ? 3 : 2 }}
              connectNulls={false}
            />
          ))}
        </LineChart>
      </Figura>

      <h2>{t("veredicto_secao_titulo")}</h2>
      <VeredictoCausal />
    </div>
  );
}
