import { useI18n } from "../lib/i18n.jsx";
import { CORES_CAMADA } from "./MapaTemporal.jsx";

const ORDEM = [
  "urbano",
  "industrial",
  "reassentamento",
  "cultivo_irrigado",
  "cultivo_sequeiro",
  "agua",
  "varzea",
  "osm_vias",
  "osm_ferrovia",
  "osm_lugares",
  "osm_aerodromo",
  "adensamento_2020_2025",
];

// Aviso da camada `adensamento_2020_2025` (ADR 0016 + Emenda 1): selo modelado, área
// não publicável (só padrão espacial), riscos R3/S2/S3. Os números (razão de
// sensibilidade, regime de publicação) vêm do manifesto — NUNCA digitados aqui.
function AvisoAdensamento({ manifest, t }) {
  const caveats = manifest?.camadas?.adensamento_2020_2025?.caveats;
  const sens = caveats?.adr_0016_sensibilidade;
  return (
    <p className="aviso-caixa aviso-caixa--atencao">
      {t("aviso_adensamento_selo")}
      {sens ? (
        <>
          {" "}
          {t("aviso_adensamento_sensibilidade_prefixo")} {sens.razao_maxima_1_decil}×
          {" — "}
          {sens.regime_publicacao}
        </>
      ) : null}
      {" "}
      {t("aviso_adensamento_riscos")}
      {!caveats ? <> {t("aviso_adensamento_sem_manifesto")}</> : null}
    </p>
  );
}

export default function PainelCamadas({ camadasAtivas, setCamadasAtivas, ano, manifest }) {
  const { t } = useI18n();

  function toggle(camada) {
    setCamadasAtivas((prev) => ({ ...prev, [camada]: !prev[camada] }));
  }

  const parAtual = `${ano - 5}-${ano}`;
  const churnDoAno = manifest?.churn_pares_temporais
    ? Object.entries(manifest.churn_pares_temporais).filter(([chave]) => chave.startsWith(`${parAtual}__`))
    : [];

  return (
    <section className="ard-card" aria-label={t("camadas")}>
      <p className="ard-kicker">{t("camadas")}</p>
      <ul className="legenda-lista">
        {ORDEM.map((camada) => (
          <li className="legenda-item" key={camada}>
            <label>
              <input
                type="checkbox"
                checked={!!camadasAtivas[camada]}
                onChange={() => toggle(camada)}
              />
              <span className="legenda-swatch" style={{ background: CORES_CAMADA[camada] }} aria-hidden="true" />
              {t(`camada_${camada}`)}
            </label>
          </li>
        ))}
      </ul>

      {camadasAtivas.urbano ? <p className="aviso-caixa">{t("aviso_urbano_comissao")}</p> : null}
      {camadasAtivas.cultivo_sequeiro ? (
        <p className="aviso-caixa aviso-caixa--atencao">{t("aviso_sequeiro")}</p>
      ) : null}
      {camadasAtivas.cultivo_sequeiro || camadasAtivas.cultivo_irrigado ? (
        <p className="aviso-caixa aviso-caixa--atencao">{t("anel_periurbano_ausente")}</p>
      ) : null}

      {camadasAtivas.adensamento_2020_2025 ? (
        <AvisoAdensamento manifest={manifest} t={t} />
      ) : null}

      {churnDoAno.length > 0 ? (
        <div style={{ marginTop: 10 }}>
          <p className="ard-kicker" style={{ marginBottom: 4 }}>{t("churn_titulo")}</p>
          {churnDoAno.map(([chave, v]) => (
            <div key={chave} style={{ fontSize: 11, marginBottom: 3 }}>
              <span className="churn-badge">{v.classe}</span>{" "}
              churn {(v.churn * 100).toFixed(0)}% · Jaccard {v.jaccard.toFixed(2)}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
