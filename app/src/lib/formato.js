// Formatação de números pelo idioma da interface (§6: PT padrão, EN).
//
// Um único ponto de formatação para que "Jaccard 0,53" em PT e "Jaccard 0.53" em EN
// saiam do mesmo valor, sem `toFixed` (que sempre usa ponto) espalhado pelos
// componentes. PT usa a convenção de Moçambique (`pt-MZ`: vírgula decimal, espaço
// como separador de milhar) — a mesma que PainelEstatisticas/DemografiaPage já usavam.
import { useMemo } from "react";
import { useI18n } from "./i18n.jsx";

export function localeDoIdioma(lang) {
  return lang === "en" ? "en" : "pt-MZ";
}

/** `casas` fixa mínimo e máximo de casas decimais; `max` só o máximo. */
export function formatarNumero(v, lang, { casas, max, sinal = false } = {}) {
  if (typeof v !== "number" || !Number.isFinite(v)) return "—";
  const opcoes =
    casas != null
      ? { minimumFractionDigits: casas, maximumFractionDigits: casas }
      : { maximumFractionDigits: max ?? 2 };
  if (sinal) opcoes.signDisplay = "exceptZero";
  return new Intl.NumberFormat(localeDoIdioma(lang), opcoes).format(v);
}

/** Fração (0–1) como porcentagem inteira pelo idioma: 0.53 → "53%" / "53%". */
export function formatarFracaoPct(v, lang, casas = 0) {
  if (typeof v !== "number" || !Number.isFinite(v)) return "—";
  return `${formatarNumero(v * 100, lang, { casas })}%`;
}

/** Hook: formatadores já ligados ao idioma atual. */
export function useFormato() {
  const { lang } = useI18n();
  return useMemo(
    () => ({
      lang,
      num: (v, opcoes) => formatarNumero(v, lang, opcoes),
      pct: (v, casas) => formatarFracaoPct(v, lang, casas),
    }),
    [lang]
  );
}
