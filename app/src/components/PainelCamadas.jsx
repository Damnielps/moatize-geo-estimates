import { useI18n } from "../lib/i18n.jsx";
import { camadaDisponivelNoAno, estiloAmostra, metaClasse } from "../lib/camadasBase.js";
import { REPO_URL } from "../lib/publicacao.js";
import { useFormato } from "../lib/formato.js";

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
function AvisoAdensamento({ manifest, t, fmt }) {
  const caveats = manifest?.camadas?.adensamento_2020_2025?.caveats;
  const sens = caveats?.adr_0016_sensibilidade;
  return (
    <p className="aviso-caixa aviso-caixa--atencao">
      {t("aviso_adensamento_selo")}
      {sens ? (
        <>
          {" "}
          {t("aviso_adensamento_sensibilidade_prefixo")} {fmt.num(sens.razao_maxima_1_decil, { max: 4 })}×
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

const URL_ADR_PALETA = `${REPO_URL}/blob/main/docs/ADR/0018-paleta-uso-do-solo-worldcover.md`;

// Dica da amostra: cor oficial WorldCover ou adaptação declarada (ADR 0018). A `nota` do YAML
// só existe em PT; em EN a dica declara a adaptação e aponta o ADR (i18n).
function dicaCor(camada, t, lang) {
  const meta = metaClasse(camada);
  if (!meta) return null;
  const molde = meta.origem === "adaptacao" ? t("legenda_adaptacao_tooltip") : t("legenda_oficial_tooltip");
  return molde
    .replace("{classe}", meta.classe_worldcover)
    .replace("{nota}", lang === "pt" ? meta.nota ?? "" : "")
    .trim();
}

export default function PainelCamadas({ camadasAtivas, setCamadasAtivas, ano, manifest }) {
  const { t, lang } = useI18n();
  const fmt = useFormato();

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
        {ORDEM.map((camada) => {
          // Camada restrita a um ano (hoje só `adensamento_2020_2025`, contraste
          // 2020→2025 MODELADO, ADR 0016): fora desse ano o checkbox fica desabilitado
          // e desmarcado na tela, mas a preferência do store é preservada — voltar a
          // 2025 a redesenha (decisão 2026-09-09 de "ligada por padrão" intacta).
          const disponivel = camadaDisponivelNoAno(camada, ano);
          const idNota = `nota-indisponivel-${camada}`;
          const meta = metaClasse(camada);
          const dica = dicaCor(camada, t, lang);
          return (
            <li className="legenda-item" key={camada}>
              <label className={disponivel ? undefined : "legenda-item--indisponivel"}>
                <input
                  type="checkbox"
                  checked={disponivel && !!camadasAtivas[camada]}
                  disabled={!disponivel}
                  aria-describedby={disponivel ? undefined : idNota}
                  onChange={() => toggle(camada)}
                />
                <span className="legenda-swatch" style={estiloAmostra(camada)} title={dica ?? undefined} aria-hidden="true" />
                <span>
                  {t(`camada_${camada}`)}
                  {meta?.origem === "adaptacao" ? (
                    <>
                      {" "}
                      <span className="legenda-adaptacao" title={dica} aria-hidden="true">
                        {t("legenda_adaptacao")}
                      </span>
                      <span className="sr-only"> ({dica})</span>
                    </>
                  ) : null}
                  {disponivel ? null : (
                    <span id={idNota} className="legenda-nota">
                      {t(`camada_${camada}_indisponivel`)}
                    </span>
                  )}
                </span>
              </label>
            </li>
          );
        })}
      </ul>
      <p className="legenda-fonte-cores">
        {t("legenda_cores_worldcover")} ·{" "}
        <a href={URL_ADR_PALETA} target="_blank" rel="noopener noreferrer">
          {t("legenda_cores_adr")}
        </a>
      </p>

      {camadasAtivas.urbano ? <p className="aviso-caixa">{t("aviso_urbano_comissao")}</p> : null}
      {camadasAtivas.cultivo_sequeiro ? (
        <p className="aviso-caixa aviso-caixa--atencao">{t("aviso_sequeiro")}</p>
      ) : null}
      {camadasAtivas.cultivo_sequeiro || camadasAtivas.cultivo_irrigado ? (
        <p className="aviso-caixa aviso-caixa--atencao">{t("anel_periurbano_ausente")}</p>
      ) : null}

      {camadasAtivas.adensamento_2020_2025 && camadaDisponivelNoAno("adensamento_2020_2025", ano) ? (
        <AvisoAdensamento manifest={manifest} t={t} fmt={fmt} />
      ) : null}

      {churnDoAno.length > 0 ? (
        <div style={{ marginTop: 10 }}>
          <p className="ard-kicker" style={{ marginBottom: 4 }}>{t("churn_titulo")}</p>
          {churnDoAno.map(([chave, v]) => (
            <div key={chave} style={{ fontSize: 11, marginBottom: 3 }}>
              <span className="churn-badge">{v.classe}</span>{" "}
              churn {fmt.pct(v.churn)} · Jaccard {fmt.num(v.jaccard, { casas: 2 })}
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
