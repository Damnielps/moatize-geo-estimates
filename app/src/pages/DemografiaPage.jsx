import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid,
  BarChart, Bar,
} from "recharts";
import { carregarCsv } from "../lib/data.js";
import { useI18n, interpolarComPartes } from "../lib/i18n.jsx";
import ProvenanciaNumero from "../components/ProvenanciaNumero.jsx";

const CORES = ["#24404F", "#9C5B41", "#3D5A4C", "#7E9BAA", "#A98A3F", "#6E3B45"];

// Ordem fixa de exibição — não altera o conteúdo do CSV, só a ordem das linhas/séries.
const ORDEM_UNIDADES = ["Cidade de Tete", "Distrito de Moatize", "Província de Tete", "Moçambique"];

const ANOS_TABELA = [1997, 2007, 2017, 2025];

function fmtNum(casas = 0) {
  return (v) => (typeof v === "number" ? v.toLocaleString("pt-MZ", { maximumFractionDigits: casas }) : "—");
}

// Ordem de "pior selo" — §10: observado é a leitura mais firme, modelado a menos.
// Um gráfico que combina pontas de selos diferentes (razão, índice multi-unidade)
// herda o PIOR dos dois, nunca o melhor nem uma etiqueta inventada como "derivado".
const ORDEM_SELO = { observado: 0, interpolado: 1, modelado: 2 };
function piorSelo(a, b) {
  if (!a) return b ?? null;
  if (!b) return a ?? null;
  return (ORDEM_SELO[a] ?? 99) >= (ORDEM_SELO[b] ?? 99) ? a : b;
}
// Selo de um cartão inteiro = união (ordenada, sem repetição) dos selos das linhas do
// CSV efetivamente plotadas nele — nunca escrito à mão no JSX.
function juntarSelos(selos) {
  const unicos = [...new Set(selos.filter(Boolean))];
  unicos.sort((a, b) => (ORDEM_SELO[a] ?? 99) - (ORDEM_SELO[b] ?? 99));
  return unicos.join(" / ") || null;
}

const ORDEM_NIVEL = { A: 0, B: 1, C: 2 };
function piorNivel(a, b) {
  if (!a) return b ?? null;
  if (!b) return a ?? null;
  return (ORDEM_NIVEL[a] ?? 99) >= (ORDEM_NIVEL[b] ?? 99) ? a : b;
}

// Busca uma coluna "desvio_pct_<variante>" por PREFIXO, não por igualdade de nome.
// Armadilha já paga duas vezes neste projeto: a coluna que traz o desvio da variante
// "diagnostico_sem_peso_construido" chama-se "desvio_pct_diagnostico_sem_peso" (SEM
// "_construido"). Casar por igualdade de nome descarta essa coluna em silêncio — e é
// justamente a variante que valida (ver docs/ADR/0017). Aqui falha alto em vez disso.
function acharDesvioPorPrefixo(row, variante) {
  const PREFIXO = "desvio_pct_";
  const chaves = Object.keys(row ?? {}).filter((k) => k.startsWith(PREFIXO));
  const chave = chaves.find(
    (k) => variante.startsWith(k.slice(PREFIXO.length)) && row[k] !== "" && row[k] != null
  );
  if (!chave) {
    throw new Error(
      `populacao_vila_moatize_sensibilidade.csv: nenhuma coluna ${PREFIXO}* compatível por prefixo com a variante "${variante}". Colunas disponíveis: ${chaves.join(", ") || "(nenhuma)"}.`
    );
  }
  return Number(row[chave]);
}

function GraficoCard({ titulo, fonte, metodo, selo, children }) {
  return (
    <div className="ard-card grafico-card">
      <h3>{titulo}</h3>
      <ResponsiveContainer width="100%" height={320}>
        {children}
      </ResponsiveContainer>
      <p className="grafico-fonte">
        <strong>Fonte:</strong> {fonte} · <strong>Método:</strong> {metodo}
        {selo ? <> · <strong>Selo:</strong> {selo}</> : null}
      </p>
    </div>
  );
}

// Marcador vazado para pontos de nível de fonte B ou C (aviso obrigatório: nível no
// tooltip, marcador diferente na tela). `payload` traz o ponto inteiro construído em
// `indiceSeries`, incluindo `nivel_<unidade>` para esta série específica.
function pontoPorNivel(chaveNivel, cor) {
  return function DotPorNivel(props) {
    const { cx, cy, payload } = props;
    const nivel = payload?.[chaveNivel];
    if (cx == null || cy == null || !payload || payload[chaveNivel.replace("nivel_", "")] == null) return null;
    const vazado = nivel === "B" || nivel === "C" || nivel === "ausente";
    return (
      <circle
        cx={cx}
        cy={cy}
        r={4}
        fill={vazado ? "#fff" : cor}
        stroke={cor}
        strokeWidth={2}
      />
    );
  };
}

export default function DemografiaPage() {
  const { t } = useI18n();
  const [linhas, setLinhas] = useState([]);
  const [carregado, setCarregado] = useState(false);
  const [vilaSensibilidade, setVilaSensibilidade] = useState([]);

  useEffect(() => {
    carregarCsv("csv/demografia_serie_1997_2025.csv").then((d) => {
      setLinhas(d);
      setCarregado(true);
    });
    carregarCsv("csv/populacao_vila_moatize_sensibilidade.csv").then(setVilaSensibilidade);
  }, []);

  const unidades = useMemo(() => {
    const presentes = [...new Set(linhas.map((r) => r.unidade_geografica))].filter(Boolean);
    // Ordem fixa primeiro, depois qualquer unidade nova que apareça no CSV sem
    // reescrever este arquivo (ex.: vila de Moatize, quando a coleta concluir).
    const extras = presentes.filter((u) => !ORDEM_UNIDADES.includes(u));
    return [...ORDEM_UNIDADES.filter((u) => presentes.includes(u)), ...extras];
  }, [linhas]);

  // Linha do CSV mais específica para (unidade, ano, prefixo de variável) — usada pela
  // tabela e pelos gráficos. Nunca inventa: se não existir, devolve undefined.
  const acha = useMemo(() => {
    return (unidade, ano, variavel) =>
      linhas.find((r) => r.unidade_geografica === unidade && r.ano === ano && r.variavel === variavel);
  }, [linhas]);

  const vilaMoatizeAusente = carregado && !unidades.includes("moatize_vila") && !unidades.includes("Vila de Moatize");

  // Sensibilidade da estimativa da Vila de Moatize — data/processed/
  // populacao_vila_moatize_sensibilidade.csv. Nenhum destes números é digitado: piso e
  // teto vêm da linha "piso_teto" da própria Vila; o desvio mínimo/máximo e o desvio da
  // variante sem peso vêm da validação cruzada do mesmo método em Cidade de Tete
  // (a única unidade deste conjunto com contagem observada para comparar).
  const vilaAviso = useMemo(() => {
    if (!vilaSensibilidade.length) return null;
    const rowPisoTeto = vilaSensibilidade.find(
      (r) => r.unidade_geografica === "Vila de Moatize" && r.metodo_peso === "piso_teto"
    );
    const rowValidacao = vilaSensibilidade.find(
      (r) => r.unidade_geografica === "Cidade de Tete" && r.metodo_peso === "validacao_cruzada"
    );
    if (!rowPisoTeto || !rowValidacao) return null;

    const VARIANTES_RESTRITAS = ["classificacao_propria", "ghsl_built_s", "pertenca_binaria", "pertenca_mediana"];
    const desvios = VARIANTES_RESTRITAS.map((v) => Math.abs(acharDesvioPorPrefixo(rowValidacao, v)));
    const desvioMin = Math.min(...desvios);
    const desvioMax = Math.max(...desvios);
    const desvioSemPeso = acharDesvioPorPrefixo(rowValidacao, "diagnostico_sem_peso_construido");

    const fmtInt = fmtNum(0);
    const fmtPct = (v) => `${v >= 0 ? "+" : ""}${v.toLocaleString("pt-MZ", { maximumFractionDigits: 2 })}%`;
    const fmtPctSemSinal = (v) => `${v.toLocaleString("pt-MZ", { maximumFractionDigits: 0 })}%`;

    const fonteCsv = "data/processed/populacao_vila_moatize_sensibilidade.csv";
    const propsBase = { fonte: fonteCsv, selo: rowPisoTeto.selo, nivelFonte: rowPisoTeto.nivel_fonte, ano: 2017 };
    const propsValidacao = { fonte: `${fonteCsv} (Cidade de Tete, validacao_cruzada)`, selo: rowValidacao.selo, nivelFonte: rowValidacao.nivel_fonte, ano: 2017 };

    return {
      partes: {
        piso: (
          <ProvenanciaNumero {...propsBase} valor={Number(rowPisoTeto.piso)} formatador={fmtInt} unidadeMedida="hab." metodo={rowPisoTeto.nota_metodo} />
        ),
        teto: (
          <ProvenanciaNumero {...propsBase} valor={Number(rowPisoTeto.teto)} formatador={fmtInt} unidadeMedida="hab." metodo={rowPisoTeto.nota_metodo} />
        ),
        desvioMin: (
          <ProvenanciaNumero {...propsValidacao} valor={desvioMin} formatador={fmtPctSemSinal} metodo={rowValidacao.nota_metodo} />
        ),
        desvioMax: (
          <ProvenanciaNumero {...propsValidacao} valor={desvioMax} formatador={fmtPctSemSinal} metodo={rowValidacao.nota_metodo} />
        ),
        desvioSemPeso: (
          <ProvenanciaNumero {...propsValidacao} valor={desvioSemPeso} formatador={fmtPct} metodo={rowValidacao.nota_metodo} />
        ),
      },
    };
  }, [vilaSensibilidade]);

  // --- Índice de crescimento — base = primeiro ano disponível de cada unidade ---
  const indiceSeries = useMemo(() => {
    const anosSet = new Set();
    const porUnidade = {};
    for (const u of unidades) {
      const linhasU = linhas.filter((r) => r.unidade_geografica === u && String(r.variavel).startsWith("indice_base_"));
      const ordenado = linhasU.slice().sort((a, b) => a.ano - b.ano);
      porUnidade[u] = {};
      for (const r of ordenado) {
        anosSet.add(r.ano);
        porUnidade[u][r.ano] = { valor: r.valor, nivel: r.nivel_fonte, selo: r.selo };
      }
    }
    const anos = [...anosSet].sort((a, b) => a - b);
    return anos.map((ano) => {
      const linha = { ano };
      for (const u of unidades) {
        const ponto = porUnidade[u][ano];
        linha[u] = ponto ? ponto.valor : null;
        linha[`nivel_${u}`] = ponto ? ponto.nivel : null;
        linha[`selo_${u}`] = ponto ? ponto.selo : null;
      }
      return linha;
    });
  }, [linhas, unidades]);

  // Um índice de um único ponto vale 100 por construção e não informa nada — a mesma
  // regra de "só nomeia quem tem série" de unidadesCagr/unidadesRitmo, aplicada aqui a
  // partir da contagem real de pontos plotados (não é caso especial da Vila no código:
  // é critério sobre os dados). A unidade continua na tabela e no aviso da Vila.
  const unidadesIndice = useMemo(
    () => unidades.filter((u) => indiceSeries.filter((d) => d[u] != null).length >= 2),
    [indiceSeries, unidades]
  );

  const seloIndice = useMemo(
    () =>
      juntarSelos(
        unidadesIndice.flatMap((u) => indiceSeries.map((d) => d[`selo_${u}`]).filter(Boolean))
      ),
    [indiceSeries, unidadesIndice]
  );

  // --- CAGR por intervalo censitário (barras agrupadas por unidade) ---
  const cagrIntervalos = [
    { chave: "cagr_1997_2007", rotulo: "1997→2007" },
    { chave: "cagr_2007_2017", rotulo: "2007→2017" },
    { chave: "cagr_2017_2025", rotulo: "2017→2025" },
  ];
  const cagrDados = useMemo(
    () =>
      cagrIntervalos.map(({ chave, rotulo }) => {
        const linha = { intervalo: rotulo };
        for (const u of unidades) {
          const row = linhas.find((r) => r.unidade_geografica === u && r.variavel === chave);
          linha[u] = row ? row.valor : null;
          linha[`nivel_${u}`] = row ? row.nivel_fonte : null;
          linha[`selo_${u}`] = row ? row.selo : null;
        }
        return linha;
      }),
    [linhas, unidades]
  );
  const seloCagr = useMemo(
    () => juntarSelos(cagrDados.flatMap((d) => unidades.map((u) => d[`selo_${u}`]))),
    [cagrDados, unidades]
  );

  // --- Ritmo relativo: CAGR(unidade) / CAGR(Moçambique) por intervalo ---
  // Um gráfico de razão herda o PIOR selo/nível das duas pontas (§10) — nunca a
  // etiqueta inventada "derivado", que não é selo válido.
  const ritmoDados = useMemo(
    () =>
      cagrIntervalos.map(({ chave, rotulo }) => {
        const nacional = linhas.find((r) => r.unidade_geografica === "Moçambique" && r.variavel === chave);
        const linha = { intervalo: rotulo };
        for (const u of unidades) {
          if (u === "Moçambique") continue;
          const row = linhas.find((r) => r.unidade_geografica === u && r.variavel === chave);
          linha[u] = row && nacional && nacional.valor ? row.valor / nacional.valor : null;
          linha[`nivel_${u}`] = row && nacional ? piorNivel(row.nivel_fonte, nacional.nivel_fonte) : null;
          linha[`selo_${u}`] = row && nacional ? piorSelo(row.selo, nacional.selo) : null;
        }
        return linha;
      }),
    [linhas, unidades]
  );
  const seloRitmo = useMemo(
    () =>
      juntarSelos(
        ritmoDados.flatMap((d) => unidades.filter((u) => u !== "Moçambique").map((u) => d[`selo_${u}`]))
      ),
    [ritmoDados, unidades]
  );

  // Uma legenda só nomeia unidade que TEM barra. A Vila de Moatize é o caso que
  // obrigou a regra: um único ano (2017), logo nenhum CAGR — e uma entrada de legenda
  // sem barra lê-se como medição faltante, quando o que existe é medição impossível.
  // A ausência da Vila aqui é dita em palavras no painel "como ler", não insinuada por
  // um espaço vazio no gráfico.
  const comValor = (dados, candidatas) =>
    candidatas.filter((u) => dados.some((d) => d[u] !== null && d[u] !== undefined));

  const unidadesCagr = useMemo(() => comValor(cagrDados, unidades), [cagrDados, unidades]);
  const unidadesRitmo = useMemo(
    () => comValor(ritmoDados, unidades.filter((u) => u !== "Moçambique")),
    [ritmoDados, unidades]
  );

  return (
    <div>
      <h2>{t("pop_titulo")}</h2>

      <section className="ard-card" aria-label={t("pop_aviso_titulo")}>
        <p className="ard-kicker">{t("pop_aviso_titulo")}</p>
        <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 13, lineHeight: 1.5 }}>
          <li>{t("pop_aviso_niveis")}</li>
          <li>{t("pop_aviso_2025")}</li>
          <li>{t("pop_aviso_moatize_limites")}</li>
          <li>{t("pop_aviso_2017_naoajustado")}</li>
          <li>{t("pop_aviso_total_nacional")}</li>
          <li>
            {vilaAviso
              ? interpolarComPartes(t("pop_aviso_vila_moatize"), vilaAviso.partes)
              : t("pop_aviso_vila_moatize")}
          </li>
        </ul>
      </section>

      <GraficoCard
        titulo={t("pop_indice_titulo")}
        fonte="data/processed/demografia_serie_1997_2025.csv, variáveis indice_base_YYYY"
        metodo="Cada unidade indexada ao seu próprio primeiro ano disponível = 100. Pontos de nível B/C: marcador vazado (nível no tooltip do gráfico do navegador; veja a tabela abaixo para proveniência completa por ProvenanciaNumero). Unidades com menos de dois pontos na série não entram neste gráfico — um índice de um único ponto vale 100 por construção e não informa ritmo (ver aviso da Vila de Moatize)."
        selo={seloIndice}
      >
        <LineChart data={indiceSeries}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--ard-filete-cl)" />
          <XAxis dataKey="ano" />
          <YAxis />
          <Tooltip />
          <Legend />
          {unidadesIndice.map((u) => (
            <Line
              key={u}
              type="monotone"
              dataKey={u}
              name={u}
              stroke={CORES[unidades.indexOf(u) % CORES.length]}
              strokeWidth={2}
              connectNulls
              dot={pontoPorNivel(`nivel_${u}`, CORES[unidades.indexOf(u) % CORES.length])}
            />
          ))}
        </LineChart>
      </GraficoCard>

      <GraficoCard
        titulo={t("pop_cagr_titulo")}
        fonte="data/processed/demografia_serie_1997_2025.csv, variáveis cagr_1997_2007/cagr_2007_2017/cagr_2017_2025"
        metodo="CAGR geométrico entre os dois anos do intervalo, lido diretamente do CSV (nunca recalculado no front-end). Nível de fonte da barra = pior nível entre as duas pontas do intervalo (ver CSV)."
        selo={seloCagr}
      >
        <BarChart data={cagrDados}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--ard-filete-cl)" />
          <XAxis dataKey="intervalo" />
          <YAxis unit=" %/ano" />
          <Tooltip
            formatter={(valor, nome, item) => [
              `${valor} %/ano (nível ${item.payload[`nivel_${nome}`] ?? "?"})`,
              nome,
            ]}
          />
          <Legend />
          {unidadesCagr.map((u) => (
            <Bar
              key={u}
              dataKey={u}
              name={u}
              fill={CORES[unidades.indexOf(u) % CORES.length]}
            />
          ))}
        </BarChart>
      </GraficoCard>

      <GraficoCard
        titulo={t("pop_ritmo_titulo")}
        fonte="derivado de data/processed/demografia_serie_1997_2025.csv (cagr_* de cada unidade ÷ cagr_* de Moçambique, mesmo intervalo)"
        metodo={t("pop_ritmo_metodo") + " Selo e nível de fonte da barra = pior selo / pior nível entre as duas pontas da razão (a unidade e Moçambique, §10) — nunca 'derivado', que não é selo válido."}
        selo={seloRitmo}
      >
        <BarChart data={ritmoDados}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--ard-filete-cl)" />
          <XAxis dataKey="intervalo" />
          <YAxis />
          <Tooltip
            formatter={(valor, nome, item) => [
              `${valor} (nível ${item.payload[`nivel_${nome}`] ?? "?"})`,
              nome,
            ]}
          />
          <Legend />
          {unidadesRitmo.map((u) => (
            <Bar
              key={u}
              dataKey={u}
              name={u}
              fill={CORES[unidades.indexOf(u) % CORES.length]}
            />
          ))}
        </BarChart>
      </GraficoCard>

      <section className="ard-card" aria-label={t("pop_tabela_titulo")}>
        <h3>{t("pop_tabela_titulo")}</h3>
        <table className="ard-tabela">
          <thead>
            <tr>
              <th>{t("unidade")}</th>
              {ANOS_TABELA.map((a) => (
                <th key={a}>{a}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {unidades.map((u) => (
              <tr key={u}>
                <td>{u}</td>
                {ANOS_TABELA.map((ano) => {
                  const row = acha(u, ano, "populacao_total_residente");
                  return (
                    <td key={ano}>
                      {row ? (
                        <ProvenanciaNumero
                          valor={row.valor}
                          unidadeMedida={row.valor != null ? "hab." : null}
                          formatador={fmtNum(0)}
                          fonte={row.fonte}
                          metodo={row.metodo}
                          ano={row.ano}
                          selo={row.selo}
                          nivelFonte={row.nivel_fonte}
                          nota={row.nota}
                        />
                      ) : (
                        "—"
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
            {vilaMoatizeAusente ? (
              <tr>
                <td>{t("pop_moatize_vila_ausente_titulo")}</td>
                <td colSpan={ANOS_TABELA.length}>{t("pop_moatize_vila_ausente_texto")}</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>
    </div>
  );
}
