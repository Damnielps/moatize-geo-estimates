import { useId, useState } from "react";
import { useI18n } from "../lib/i18n.jsx";

const SELO_LABEL = {
  observado: { pt: "observado", en: "observed" },
  interpolado: { pt: "interpolado", en: "interpolated" },
  modelado: { pt: "modelado", en: "modeled" },
};

/**
 * Todo número quantitativo do app passa por aqui (CLAUDE.md §6: "cada número abre
 * tooltip com fonte, ano, método e nível de confiança"). Um número sem `fonte` não
 * deve ser renderizado por este componente sem o aviso "sem proveniência".
 */
export default function ProvenanciaNumero({
  valor,
  unidadeMedida,
  fonte,
  metodo,
  ano,
  selo,
  nivelFonte,
  nota,
  formatador,
}) {
  const { lang, t } = useI18n();
  const [aberto, setAberto] = useState(false);
  const id = useId();
  const texto = formatador ? formatador(valor) : valor;
  const semFonte = !fonte;

  return (
    <span className="prov-wrap">
      <button
        type="button"
        className={`prov-valor${semFonte ? " prov-valor--sem-fonte" : ""}`}
        aria-describedby={aberto ? id : undefined}
        aria-expanded={aberto}
        onClick={() => setAberto((v) => !v)}
        onBlur={() => setAberto(false)}
      >
        {texto}
        {unidadeMedida ? <span className="prov-unidade"> {unidadeMedida}</span> : null}
        <sup className="prov-marca">†</sup>
      </button>
      {aberto ? (
        <span role="tooltip" id={id} className="prov-tooltip">
          {semFonte ? (
            <strong>{lang === "pt" ? "Sem proveniência declarada." : "No declared provenance."}</strong>
          ) : (
            <>
              <div>
                <strong>{t("fonte")}:</strong> {fonte}
              </div>
              {metodo ? (
                <div>
                  <strong>{t("metodo")}:</strong> {metodo}
                </div>
              ) : null}
              {ano != null ? (
                <div>
                  <strong>{t("ano_dado")}:</strong> {ano}
                </div>
              ) : null}
              {selo ? (
                <div>
                  <strong>{t("selo")}:</strong>{" "}
                  <span className={`ard-pill ard-pill--${selo === "observado" ? "conforme" : selo === "modelado" ? "atencao" : "semdado"}`}>
                    {SELO_LABEL[selo]?.[lang] ?? selo}
                  </span>
                </div>
              ) : null}
              {nivelFonte ? (
                <div>
                  <strong>{t("nivel")}:</strong> nível {nivelFonte}
                </div>
              ) : null}
              {nota ? <div className="prov-nota">{nota}</div> : null}
            </>
          )}
        </span>
      ) : null}
    </span>
  );
}
