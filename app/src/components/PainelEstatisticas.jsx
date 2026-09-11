import { useEffect, useState } from "react";
import { carregarCsv } from "../lib/data.js";
import { useI18n } from "../lib/i18n.jsx";
import { formatarNumero } from "../lib/formato.js";
import ProvenanciaNumero from "./ProvenanciaNumero.jsx";

const UNIDADES_SELECIONAVEIS = [
  "Cidade de Tete",
  "Distrito de Moatize",
  "moatize_vila",
  "cateme",
  "mwaladzi",
  "industrial",
  "aoi",
];

// Formatação pelo idioma da interface (lib/formato.js): PT vírgula decimal, EN ponto.
function fmtNumLang(lang, casas = 2) {
  return (v) => (typeof v === "number" ? formatarNumero(v, lang, { max: casas }) : v);
}

function KpiCard({ rotulo, sufixo, ...props }) {
  return (
    <div className="ard-card" style={{ padding: "10px 12px" }}>
      <p className="ard-kpi-label">{rotulo}</p>
      <p className="ard-kpi-value" style={{ fontSize: 20 }}>
        <ProvenanciaNumero {...props} />
        {sufixo ? <span style={{ fontSize: 15, opacity: 0.75 }}>{sufixo}</span> : null}
      </p>
    </div>
  );
}

export default function PainelEstatisticas({ ano, unidade, setUnidade }) {
  const { t, lang } = useI18n();
  const fmtNum = (casas) => fmtNumLang(lang, casas);
  const [stats, setStats] = useState([]);
  const [areaConstruida, setAreaConstruida] = useState([]);
  const [pegada, setPegada] = useState([]);
  const [cultivo, setCultivo] = useState([]);
  const [cultivoVarzea, setCultivoVarzea] = useState([]);
  const [acuraciaConstruido, setAcuraciaConstruido] = useState([]);

  useEffect(() => {
    carregarCsv("csv/stats_by_year_by_unit.csv").then(setStats);
    carregarCsv("csv/area_construida_por_ano.csv").then(setAreaConstruida);
    carregarCsv("csv/pegada_por_ano.csv").then(setPegada);
    carregarCsv("csv/cultivo_por_ano.csv").then(setCultivo);
    carregarCsv("csv/cultivo_varzea_por_ano.csv").then(setCultivoVarzea);
    carregarCsv("csv/acuracia_por_ano.csv").then(setAcuraciaConstruido);
  }, []);

  const linhasUnidade = stats.filter((r) => r.unidade_geografica === unidade && r.ano === ano);
  const linhaArea = areaConstruida.find((r) => r.ano === ano);
  const linhasPegada = pegada.filter((r) => r.ano === ano);
  const linhaCultivo = cultivo.find((r) => r.ano === ano);
  const linhaCultivoVarzea = cultivoVarzea.find((r) => r.ano === ano);
  const linhaAcuracia = acuraciaConstruido.find((r) => r.ano === ano);

  return (
    <section className="painel-lateral" aria-label={t("unidade")}>
      <div className="ard-card">
        <label htmlFor="select-unidade" style={{ display: "block", fontWeight: 600, fontSize: 12, marginBottom: 4 }}>
          {t("unidade")}
        </label>
        <select id="select-unidade" value={unidade} onChange={(e) => setUnidade(e.target.value)} style={{ width: "100%", padding: 6 }}>
          {UNIDADES_SELECIONAVEIS.map((u) => (
            <option key={u} value={u}>{u}</option>
          ))}
        </select>
      </div>

      {linhasUnidade.length > 0 ? (
        <div className="ard-card">
          <p className="ard-kicker">{t("kpi_demografia")} — {unidade} · {ano}</p>
          <div className="kpi-grid">
            {linhasUnidade.slice(0, 8).map((r, i) => (
              <KpiCard
                key={i}
                rotulo={r.variavel}
                valor={r.valor}
                unidadeMedida={r.unidade_medida}
                fonte={r.fonte}
                metodo={r.metodo}
                ano={r.ano}
                selo={r.selo}
                nivelFonte={r.nivel_fonte}
                nota={r.nota}
                formatador={fmtNum(3)}
              />
            ))}
          </div>
          {linhasUnidade.length > 8 ? (
            <details style={{ marginTop: 8 }}>
              <summary style={{ cursor: "pointer", fontSize: 12 }}>
                +{linhasUnidade.length - 8} variáveis
              </summary>
              <div className="kpi-grid" style={{ marginTop: 8 }}>
                {linhasUnidade.slice(8).map((r, i) => (
                  <KpiCard
                    key={i}
                    rotulo={r.variavel}
                    valor={r.valor}
                    unidadeMedida={r.unidade_medida}
                    fonte={r.fonte}
                    metodo={r.metodo}
                    ano={r.ano}
                    selo={r.selo}
                    nivelFonte={r.nivel_fonte}
                    nota={r.nota}
                    formatador={fmtNum(3)}
                  />
                ))}
              </div>
            </details>
          ) : null}
        </div>
      ) : (
        <p style={{ fontSize: 12, color: "var(--ard-text-3)" }}>
          {t("kpi_sem_linhas")}
        </p>
      )}

      {linhaArea ? (
        <div className="ard-card">
          <p className="ard-kicker">{t("kpi_area_construida")} · {ano}</p>
          <div className="kpi-grid">
            <KpiCard rotulo="urbano" valor={linhaArea.urbano_km2} unidadeMedida="km²" selo={linhaArea.selo}
              fonte="Classificação própria (Landsat/Sentinel-2), R1+R2" ano={ano}
              nota={linhaArea.nota} formatador={fmtNum(2)} />
            <KpiCard rotulo="industrial (pegada)" valor={linhaArea.industrial_km2} unidadeMedida="km²" selo={linhaArea.selo}
              fonte="Classificação própria" ano={ano} nota={linhaArea.nota} formatador={fmtNum(2)} />
            <KpiCard rotulo="reassentamento (pegada)" valor={linhaArea.reassentamento_km2} unidadeMedida="km²" selo={linhaArea.selo}
              fonte="Classificação própria" ano={ano} nota={linhaArea.nota} formatador={fmtNum(2)} />
          </div>
        </div>
      ) : null}

      {linhasPegada.length ? (
        <div className="ard-card">
          <p className="ard-kicker">{t("kpi_pegada")} · {ano}</p>
          {linhasPegada.map((r, i) => (
            <div key={i} style={{ marginBottom: 6 }}>
              <strong style={{ fontSize: 12 }}>{r.camada}: </strong>
              <ProvenanciaNumero valor={r.area_publicada_km2} unidadeMedida="km²" selo={r.selo}
                fonte="Classificação própria (pegada, ADR 0011/0014)" ano={ano} nota={r.nota}
                formatador={fmtNum(3)} />
            </div>
          ))}
        </div>
      ) : null}

      {linhaCultivo ? (
        <div className="ard-card">
          <p className="ard-kicker">{t("kpi_agricultura")} · {ano}</p>
          <div className="kpi-grid">
            <KpiCard rotulo="cultivo irrigado" valor={linhaCultivo.cultivo_irrigado_km2} unidadeMedida="km²"
              selo={linhaCultivo.selo} fonte="Fenologia NDVI própria" ano={ano} nota={linhaCultivo.nota_instabilidade}
              formatador={fmtNum(2)} />
            <KpiCard rotulo="vegetação sazonal (não confirmada)" valor={linhaCultivo.cultivo_sequeiro_km2} unidadeMedida="km²"
              selo={linhaCultivo.selo} fonte="Fenologia NDVI própria — ADR 0012" ano={ano} nota={linhaCultivo.nota_instabilidade}
              formatador={fmtNum(2)} />
          </div>
          {linhaCultivoVarzea ? (
            <p style={{ fontSize: 12, marginTop: 6 }}>
              Fração da classe irrigada em várzea:{" "}
              <ProvenanciaNumero valor={linhaCultivoVarzea.fracao_irrigado_em_varzea * 100} unidadeMedida="%"
                selo={linhaCultivoVarzea.selo} fonte="varzea.py (HAND aproximado)" ano={ano}
                nota={linhaCultivoVarzea.nota} formatador={fmtNum(1)} />
            </p>
          ) : null}
        </div>
      ) : null}

      {linhaAcuracia ? (
        <div className="ard-card">
          <p className="ard-kicker">{t("kpi_acuracia")} · {ano}</p>
          {/* §10 e docs/ADR/0009: acurácia POR CLASSE vai com IC95 e prevalência.
              Sem os dois o número não é interpretável — exibi-lo sozinho convida o
              leitor a comparar anos que não são comparáveis. */}
          <div className="kpi-grid">
            <KpiCard rotulo="acurácia do usuário (± IC95)"
              valor={linhaAcuracia.acuracia_usuario_construido}
              fonte="Olofsson et al. 2014, validação própria" ano={ano}
              nota={linhaAcuracia.nota} formatador={fmtNum(3)}
              sufixo={linhaAcuracia.ic95_acuracia_usuario_construido
                ? ` ± ${fmtNum(3)(linhaAcuracia.ic95_acuracia_usuario_construido)}`
                : null} />
            <KpiCard rotulo="prevalência da classe no mapa"
              valor={linhaAcuracia.peso_area_construido_mapa_atual}
              fonte="validação própria" ano={ano} nota={linhaAcuracia.nota}
              formatador={(v) => `${fmtNum(2)(Number(v) * 100)} %`} />
            <KpiCard rotulo="acurácia global (não é critério)"
              valor={linhaAcuracia.acuracia_global}
              fonte="Olofsson et al. 2014" ano={ano} nota={linhaAcuracia.nota}
              formatador={fmtNum(3)} />
          </div>
          <p className="aviso-caixa aviso-caixa--atencao">{t("aviso_ic_acuracia")}</p>
        </div>
      ) : null}
    </section>
  );
}
