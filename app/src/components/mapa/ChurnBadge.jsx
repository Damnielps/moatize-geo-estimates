import { useMemo } from "react";
import ProvenanciaNumero from "../ProvenanciaNumero.jsx";
import { Termo } from "../ui.jsx";
import { useI18n } from "../../lib/i18n.jsx";
import { useFormato } from "../../lib/formato.js";

/**
 * Ao lado do ano exibido: churn e Jaccard da classe `construido` entre o ano-âncora
 * anterior e o ano atual (`manifest.churn_pares_temporais["<anoAnterior>-<ano>__construido"]`,
 * ver data/processed/app/imagery/manifest.json — chave real confirmada nesta tarefa).
 * A troca de ano no mapa é um CORTE DISCRETO (ADR 0013): este badge existe para que
 * essa instabilidade apareça ao lado do ano, não só no painel de camadas.
 */
export default function ChurnBadge({ ano, anoAnterior, manifest }) {
  const { t, lang } = useI18n();
  // Números pelo idioma (PT: "0,53"; EN: "0.53") — nunca `toFixed`, que fixa o ponto.
  const fmt = useFormato();

  const entrada = useMemo(() => {
    if (anoAnterior == null || !manifest?.churn_pares_temporais) return null;
    const chave = `${anoAnterior}-${ano}__construido`;
    return manifest.churn_pares_temporais[chave] ?? null;
  }, [ano, anoAnterior, manifest]);

  if (anoAnterior == null) {
    return (
      <span className="churn-badge churn-badge--primeiro">
        {t("churn_primeiro_ano_ancora")}
      </span>
    );
  }

  if (!entrada) {
    return (
      <span className="churn-badge churn-badge--semdado">{t("churn_sem_dado")}</span>
    );
  }

  const fonte = manifest?.gerado_por
    ? `data/processed/app/imagery/manifest.json (${manifest.gerado_por})`
    : "data/processed/app/imagery/manifest.json";

  return (
    <span className="churn-badge" title={t("churn_titulo_curto")}>
      <Termo id="churn">{t("churn_rotulo_curto")}</Termo>{" "}
      <ProvenanciaNumero
        valor={entrada.churn}
        formatador={(v) => fmt.pct(v)}
        fonte={fonte}
        metodo={entrada.nota}
        ano={entrada.par_anos}
        selo="observado"
        nota={t("churn_experimental_nota")}
      />
      {" · "}
      {t("churn_jaccard_rotulo")}{" "}
      <ProvenanciaNumero
        valor={entrada.jaccard}
        formatador={(v) => fmt.num(v, { casas: 2 })}
        fonte={fonte}
        metodo={entrada.nota}
        ano={entrada.par_anos}
        selo="observado"
        nota={lang === "pt" ? "EXPERIMENTAL — ver docs/ADR/0013." : "EXPERIMENTAL — see docs/ADR/0013."}
      />
    </span>
  );
}
