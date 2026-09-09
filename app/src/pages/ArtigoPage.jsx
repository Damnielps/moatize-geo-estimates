import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import artigo from "../content/artigo.json";
import { useI18n } from "../lib/i18n.jsx";
import { urlDownload } from "../lib/data.js";

// A aba Artigo renderiza `app/src/content/artigo.json`, GERADO por
// `pipeline/05_app/gerar_artigo.py` a partir de `paper/artigo.md` — regra que não pode
// ser quebrada (ver o próprio arquivo do script): o texto abaixo nunca é escrito ou
// copiado à mão neste componente, só formatado.

// Mesmo algoritmo de slug do script de geração (pipeline/05_app/gerar_artigo.py →
// slugificar()), para que os `id` de cabeçalho gerados aqui, em runtime, batam com os
// slugs já calculados no sumário do JSON — sem lista de âncoras mantida em paralelo.
function slugificar(titulo) {
  let texto = String(titulo).trim().toLowerCase();
  texto = texto.replace(/[`*_]/g, "");
  texto = texto.replace(/[^\p{L}\p{N}\s-]/gu, "");
  texto = texto.replace(/\s+/g, "-").replace(/^-+|-+$/g, "");
  return texto;
}

function useContadorDeSlugsRepetidos() {
  const vistos = new Map();
  return (titulo) => {
    const base = slugificar(titulo);
    const n = vistos.get(base) ?? 0;
    vistos.set(base, n + 1);
    return n === 0 ? base : `${base}-${n}`;
  };
}

function Sumario({ sumario, lang }) {
  return (
    <nav className="ard-card artigo-sumario" aria-label={lang === "pt" ? "Sumário do artigo" : "Article table of contents"}>
      <p className="ard-kicker">{lang === "pt" ? "Sumário" : "Contents"}</p>
      <ol>
        {sumario
          .filter((s) => s.nivel <= 2)
          .map((s) => (
            <li key={s.slug} className={`artigo-sumario-nivel-${s.nivel}`}>
              <a href={`#${s.slug}`}>{s.titulo}</a>
            </li>
          ))}
      </ol>
    </nav>
  );
}

export default function ArtigoPage() {
  const { lang, t } = useI18n();
  const proximoSlug = useContadorDeSlugsRepetidos();

  const componentesMarkdown = {};
  for (const nivel of [1, 2, 3, 4, 5, 6]) {
    const Tag = `h${nivel}`;
    componentesMarkdown[Tag] = ({ children, ...props }) => {
      const texto = Array.isArray(children) ? children.join("") : String(children ?? "");
      const id = proximoSlug(texto);
      return (
        <Tag id={id} {...props}>
          {children}
        </Tag>
      );
    };
  }
  // Tabelas GFM ganham wrapper com rolagem horizontal própria (§6-A: "tabelas com
  // rolagem horizontal própria"), sem alterar a medida de linha do corpo de texto.
  componentesMarkdown.table = ({ children, ...props }) => (
    <div className="artigo-tabela-scroll">
      <table {...props}>{children}</table>
    </div>
  );

  return (
    <div className="artigo-layout">
      <h2>{t("nav_artigo")}</h2>
      <p className="aviso-caixa">{artigo.aviso}</p>
      <p style={{ fontSize: 12, color: "var(--ard-text-3)" }}>
        gerado_por: <code>{artigo.gerado_por}</code> · fonte: <code>{artigo.fonte}</code> ·{" "}
        gerado em {artigo.gerado_em_utc} ·{" "}
        <a href={urlDownload("paper/artigo.md")} download>
          {lang === "pt" ? "baixar o manuscrito (.md)" : "download manuscript (.md)"}
        </a>
      </p>

      <div className="artigo-corpo-layout">
        <Sumario sumario={artigo.sumario} lang={lang} />
        <article className="artigo-corpo">
          <ReactMarkdown remarkPlugins={[remarkGfm]} components={componentesMarkdown}>
            {artigo.markdown}
          </ReactMarkdown>
        </article>
      </div>
    </div>
  );
}
