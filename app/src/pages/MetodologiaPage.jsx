import metodologia from "../content/metodologia.json";
import { useI18n } from "../lib/i18n.jsx";
import PainelDownloads from "../components/PainelDownloads.jsx";

function Secao({ titulo, corpoLinhas }) {
  return (
    <details className="adr-card">
      <summary>{titulo}</summary>
      <pre>{corpoLinhas.join("\n")}</pre>
    </details>
  );
}

export default function MetodologiaPage() {
  const { t } = useI18n();
  const dep = metodologia.ambiente;

  return (
    <div>
      <h2>{t("nav_metodologia")}</h2>
      <p className="aviso-caixa">{metodologia.aviso}</p>
      <p style={{ fontSize: 12, color: "var(--ard-text-3)" }}>
        gerado_por: <code>{metodologia.gerado_por}</code> · gerado em {metodologia.gerado_em_utc}
      </p>

      <section className="metodo-secao">
        <h3>{t("metod_ambiente_titulo")}</h3>
        <p>
          Gerenciador: {dep.gerenciador} · Python: <code>{dep.python_requires}</code> ·{" "}
          {dep.total_pacotes_no_lockfile} pacotes travados em <code>uv.lock</code>.
        </p>
        <table>
          <thead>
            <tr><th>Biblioteca</th><th className="num">Versão (uv.lock)</th><th>Categoria</th></tr>
          </thead>
          <tbody>
            {[...dep.dependencias_criticas, ...dep.dependencias_adicionais].map((d) => (
              <tr key={d.nome}>
                <td><code>{d.nome}</code></td>
                <td className="num">{d.versao ?? "ausente do lockfile"}</td>
                <td>{d.categoria}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="metodo-secao">
        <h3>{t("metod_adr_titulo")}</h3>
        <p>{metodologia.decisoes_metodologicas.nota}</p>
        {metodologia.decisoes_metodologicas.todos_os_adrs.map((a) => (
          <details key={a.numero} className="adr-card" open={a.muda_a_resposta_do_estudo}>
            <summary>
              ADR {a.numero} — {a.titulo}
              {a.muda_a_resposta_do_estudo ? <span className="ard-pill ard-pill--atencao" style={{ marginLeft: 8 }}>mudou a resposta do estudo</span> : null}
            </summary>
            <pre>{a.texto_completo_linhas.join("\n")}</pre>
          </details>
        ))}
      </section>

      <section className="metodo-secao">
        <h3>{t("metod_provenance_titulo")}</h3>
        {metodologia.proveniencia.provenance_md.map((s, i) => (
          <Secao key={i} titulo={s.titulo} corpoLinhas={s.corpo_linhas} />
        ))}
      </section>

      <section className="metodo-secao">
        <h3>{t("metod_audit_titulo")}</h3>
        {metodologia.auditoria_de_dados.data_audit_md.map((s, i) => (
          <Secao key={i} titulo={s.titulo} corpoLinhas={s.corpo_linhas} />
        ))}
      </section>

      <PainelDownloads />
    </div>
  );
}
