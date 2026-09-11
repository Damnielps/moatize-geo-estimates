import { useState } from "react";
import { useI18n } from "../lib/i18n.jsx";
import { DOI, SITE_URL, referenciaAbnt } from "../lib/publicacao.js";

/**
 * Bloco "Como citar": referência ABNT (PT/EN), link do DOI quando existir (senão a URL
 * do site), botão "Copiar" com navigator.clipboard em try/catch (§6-A, CLAUDE.md).
 */
export default function ComoCitar() {
  const { lang, t } = useI18n();
  const [copiado, setCopiado] = useState(false);
  const [erroCopia, setErroCopia] = useState(false);
  const referencia = referenciaAbnt(lang);
  const linkHref = DOI ? `https://doi.org/${DOI}` : SITE_URL;
  const linkTexto = DOI ? `${t("como_citar_doi")}: ${DOI}` : SITE_URL;

  async function copiar() {
    setErroCopia(false);
    try {
      await navigator.clipboard.writeText(referencia);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2500);
    } catch {
      setErroCopia(true);
    }
  }

  return (
    <div className="como-citar">
      <p className="ard-kicker">{t("como_citar_titulo")}</p>
      <blockquote className="ard-quote">
        {referencia}{" "}
        <a href={linkHref} target="_blank" rel="noopener noreferrer">
          {linkTexto}
        </a>
      </blockquote>
      <button type="button" onClick={copiar}>
        {copiado ? t("como_citar_copiado") : t("como_citar_copiar")}
      </button>
      {erroCopia && (
        <p className="erro" role="alert">
          {t("como_citar_falhou")}
        </p>
      )}
    </div>
  );
}
