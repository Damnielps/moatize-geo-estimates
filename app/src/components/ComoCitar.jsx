import { useState } from "react";
import { useI18n } from "../lib/i18n.jsx";
import { AUTOR, DOI, referenciaAbnt, referenciaPartes } from "../lib/publicacao.js";

/**
 * Bloco "Como citar": referência ABNT (PT/EN), ORCID do autor, link do DOI quando
 * existir (senão a URL do site e a razão de ainda não haver DOI), botão "Copiar" com
 * navigator.clipboard em try/catch (§6-A, CLAUDE.md).
 */
export default function ComoCitar() {
  const { lang, t } = useI18n();
  const [copiado, setCopiado] = useState(false);
  const [erroCopia, setErroCopia] = useState(false);
  const referencia = referenciaAbnt(lang);
  const { corpo, acesso } = referenciaPartes(lang);

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
        {corpo}{" "}
        <a href={acesso.href} target="_blank" rel="noopener noreferrer">
          {acesso.rotulo}
        </a>
        .
      </blockquote>
      <p className="como-citar__orcid">
        {t("como_citar_autor")}: {AUTOR.nome} · ORCID{" "}
        <a
          href={`https://orcid.org/${AUTOR.orcid}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          {AUTOR.orcid}
        </a>
      </p>
      {!DOI && <p className="como-citar__sem-doi">{t("como_citar_sem_doi")}</p>}
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
