// Renderização dos marcadores `{nome}` resolvidos por lib/marcadores.js. Todo número da
// página inicial passa por ProvenanciaNumero (tooltip com fonte, ano, método, selo e
// nível). Marcador com erro: em desenvolvimento, o erro aparece na própria frase (falha
// visível); em produção, traço com aviso — nunca um número de reserva.
import ProvenanciaNumero from "../ProvenanciaNumero.jsx";
import { interpolarComPartes, useI18n } from "../../lib/i18n.jsx";

export function NumeroMarcador({ r, nome }) {
  const { t } = useI18n();
  if (!r) {
    return import.meta.env.DEV ? (
      <span className="marcador-erro" role="alert">
        [{nome}: {t("inicio_marcador_nao_declarado")}]
      </span>
    ) : (
      <span className="marcador-traco" title={t("inicio_marcador_indisponivel")}>
        —
      </span>
    );
  }
  if (r.erro) {
    return import.meta.env.DEV ? (
      <span className="marcador-erro" role="alert">
        [{r.nome}: {r.erro}]
      </span>
    ) : (
      <span className="marcador-traco" title={t("inicio_marcador_indisponivel")}>
        —<span className="sr-only"> ({t("inicio_marcador_indisponivel")})</span>
      </span>
    );
  }
  return (
    <ProvenanciaNumero
      valor={r.texto}
      fonte={r.fonte}
      metodo={r.metodo}
      ano={r.ano}
      selo={r.selo}
      nivelFonte={r.nivel_fonte}
      nota={r.nota}
    />
  );
}

/** Molde com `{nome}` → texto com cada marcador trocado pelo número com proveniência. */
export function TextoMarcado({ molde, resolvidos }) {
  if (!molde) return null;
  const partes = {};
  for (const [, nome] of molde.matchAll(/\{(\w+)\}/g)) {
    partes[nome] = <NumeroMarcador r={resolvidos?.[nome]} nome={nome} />;
  }
  return <>{interpolarComPartes(molde, partes)}</>;
}
