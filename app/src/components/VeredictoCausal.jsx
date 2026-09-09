import { useEffect, useState } from "react";
import { carregarCsv } from "../lib/data.js";
import { useI18n } from "../lib/i18n.jsx";

export default function VeredictoCausal() {
  const { t } = useI18n();
  const [linhas, setLinhas] = useState([]);
  const [permutacao, setPermutacao] = useState([]);

  useEffect(() => {
    carregarCsv("causal/veredito_fase3.csv").then((rows) =>
      setLinhas(rows.filter((r) => r.bloco === "criterio_F"))
    );
    carregarCsv("causal/did_efeitos.csv").then(setPermutacao);
  }, []);

  return (
    <section className="ard-card" aria-label={t("veredito_causal_titulo")}>
      <p className="ard-kicker">{t("veredito_causal_titulo")}</p>
      <p className="aviso-caixa">{t("veredito_aviso")}</p>
      <p className="aviso-caixa aviso-caixa--atencao">{t("decomposicao_aviso")}</p>
      <p className="aviso-caixa aviso-caixa--atencao">{t("piso_p_aviso")}</p>
      {linhas.length ? (
        <table>
          <thead>
            <tr><th>Série</th><th>Quebra</th><th>Veredito</th></tr>
          </thead>
          <tbody>
            {linhas.map((r, i) => (
              <tr key={i}>
                <td>{r.serie}</td>
                <td className="num">{r.quebra}</td>
                <td>{r.veredito}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
      {permutacao.length ? (
        <table style={{ marginTop: 10 }}>
          <caption style={{ textAlign: "left", fontSize: 12, marginBottom: 4 }}>
            {t("p_permutacao_titulo")}
          </caption>
          <thead>
            <tr>
              <th>Painel</th><th>Quebra</th><th>p (permutação)</th><th>Piso de p (1 tratado / 5 doadores)</th>
            </tr>
          </thead>
          <tbody>
            {permutacao.map((r, i) => (
              <tr key={i}>
                <td>{r.painel}</td>
                <td className="num">{r.quebra}</td>
                <td className="num">{r.p_permutacao}</td>
                <td className="num">{r.piso_de_p_por_permutacao}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </section>
  );
}
