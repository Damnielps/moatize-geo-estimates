// Narrativa guiada da página inicial (Fase 4b, B3): texto rolando à esquerda, mapa fixo
// à direita; o passo no centro da tela (IntersectionObserver, rootMargin -45%/-45%)
// comanda o ano do mapa. Desenho portado de urban-canaa/web/src/tabs/Inicio.tsx.
// Conteúdo: app/src/content/narrativa.json (aprovado; não reescrito aqui). Os números
// são marcadores resolvidos contra data/processed/ (lib/marcadores.js).
//
// Rolagem: a área rolável do app é `.ard-rolagem` (App.jsx), não a janela — o observador
// usa esse elemento como raiz, e o `position: sticky` do mapa é relativo a ele.
// `prefers-reduced-motion`: sem rolagem guiada; um capítulo por vez com botões
// anterior/próximo e o mapa sem animação de enquadramento.
import { useEffect, useRef, useState } from "react";
import MapaNarrativa from "./MapaNarrativa.jsx";
import { TextoMarcado } from "./Marcador.jsx";
import ProvenanciaNumero from "../ProvenanciaNumero.jsx";
import { useI18n } from "../../lib/i18n.jsx";

function useMovimentoReduzido() {
  const consulta = "(prefers-reduced-motion: reduce)";
  const [reduzido, setReduzido] = useState(
    () => typeof window !== "undefined" && !!window.matchMedia?.(consulta).matches
  );
  useEffect(() => {
    const mq = window.matchMedia?.(consulta);
    if (!mq) return;
    const aoMudar = () => setReduzido(mq.matches);
    mq.addEventListener("change", aoMudar);
    return () => mq.removeEventListener("change", aoMudar);
  }, []);
  return reduzido;
}

function porIdioma(obj, campo, lang) {
  return obj[`${campo}_${lang}`] ?? obj[`${campo}_pt`];
}

function RotuloNivel({ nivel }) {
  const { t } = useI18n();
  if (!nivel || nivel === "A") return null;
  const texto =
    nivel === "secundario"
      ? t("slider_nivel_secundario")
      : nivel === "C"
        ? t("slider_nivel_c")
        : nivel === "B"
          ? t("inicio_nivel_b")
          : nivel;
  const classe = nivel === "C" ? "critico" : "atencao";
  return <span className={`ard-pill ard-pill--${classe} narrativa__nivel`}>{texto}</span>;
}

function MarcosDoPeriodo({ ids, marcos }) {
  const { t, lang } = useI18n();
  const lista = (ids ?? []).map((id) => ({ id, m: marcos.get(id) }));
  if (!lista.length) return null;
  return (
    <div className="narrativa__marcos">
      <p className="narrativa__rotulo">{t("inicio_marcos_rotulo")}</p>
      <ul>
        {lista.map(({ id, m }) =>
          m ? (
            <li key={id}>
              <span className="narrativa__marco-ano">
                <ProvenanciaNumero
                  valor={String(m.inicio).slice(0, 4) + (m.fim ? `–${String(m.fim).slice(0, 4)}` : "")}
                  fonte={m.fonte}
                  nivelFonte={m.nivel}
                  nota={[m.url && m.url.startsWith("http") ? m.url : null, m.nota].filter(Boolean).join(" · ")}
                />
              </span>{" "}
              <span className="narrativa__marco-tipo">{t(`marco_tipo_${m.tipo}`)}</span>{" "}
              <span>{lang === "en" ? m.rotulo_en ?? m.rotulo_pt : m.rotulo_pt}</span>{" "}
              <RotuloNivel nivel={m.nivel} />
            </li>
          ) : (
            <li key={id} className="marcador-erro" role="alert">
              [{id}: {t("inicio_marco_ausente")}]
            </li>
          )
        )}
      </ul>
    </div>
  );
}

function RefsPasso({ refs }) {
  const { t, lang } = useI18n();
  if (!refs?.length) return null;
  return (
    <div className="narrativa__refs">
      <p className="narrativa__rotulo">{t("inicio_na_literatura")}</p>
      {refs.map((r) => (
        <blockquote key={r.citacao_curta} className="ard-quote narrativa__citacao">
          {porIdioma(r, "achado", lang)} <cite>({r.citacao_curta})</cite>
        </blockquote>
      ))}
    </div>
  );
}

function Passo({ cap, i, ativo, resolvidos, marcos, refPasso, aoFocar }) {
  const { t, lang } = useI18n();
  const titulo = porIdioma(cap, "titulo", lang);
  return (
    <article
      ref={refPasso}
      data-i={i}
      className={"narrativa__passo" + (ativo ? " ativo" : "")}
      aria-current={ativo ? "step" : undefined}
      aria-labelledby={`passo-${cap.id}`}
      onFocus={aoFocar}
    >
      <p className="ard-kicker">{cap.periodo}</p>
      <h3 id={`passo-${cap.id}`}>
        <TextoMarcado molde={titulo} resolvidos={resolvidos} />
      </h3>
      <div className="narrativa__texto">
        {(porIdioma(cap, "paragrafos", lang) ?? []).map((p, k) => (
          <p key={k}>
            <TextoMarcado molde={p} resolvidos={resolvidos} />
          </p>
        ))}
      </div>
      <MarcosDoPeriodo ids={cap.marcos_ids} marcos={marcos} />
      <RefsPasso refs={cap.refs} />
      <a className="narrativa__link" href={`#/mancha?ano=${cap.ano_mapa}`}>
        {t("inicio_explorar_ano").replace("{ano}", String(cap.ano_mapa))}
      </a>
    </article>
  );
}

export default function Narrativa({ capitulos, resolvidosPorCap, marcos }) {
  const { t, lang } = useI18n();
  const reduzido = useMovimentoReduzido();
  const [passo, setPasso] = useState(0);
  const passosRef = useRef([]);
  const secaoRef = useRef(null);

  // Qual passo está no centro da área rolável (a faixa de 10 % no meio).
  useEffect(() => {
    if (reduzido || typeof IntersectionObserver === "undefined") return;
    const raiz = secaoRef.current?.closest(".ard-rolagem") ?? null;
    const obs = new IntersectionObserver(
      (entradas) => {
        for (const e of entradas) if (e.isIntersecting) setPasso(Number(e.target.dataset.i));
      },
      { root: raiz, rootMargin: "-45% 0px -45% 0px" }
    );
    passosRef.current.forEach((p) => p && obs.observe(p));
    return () => obs.disconnect();
  }, [reduzido, capitulos.length]);

  const atual = capitulos[passo] ?? capitulos[0];
  const rotuloMapa = t("inicio_mapa_rotulo")
    .replace("{ano}", String(atual.ano_mapa))
    .replace("{titulo}", porIdioma(atual, "titulo", lang));

  const mapa = (
    <div className="narrativa__fixo">
      <MapaNarrativa
        ano={atual.ano_mapa}
        anoFantasma={atual.ano_fantasma}
        camadas={atual.camadas_mapa ?? []}
        rotulo={rotuloMapa}
      />
      <p className="narrativa__credito">{t("inicio_mapa_credito")}</p>
    </div>
  );

  if (reduzido) {
    return (
      <section ref={secaoRef} className="narrativa narrativa--reduzida" aria-label={t("inicio_narrativa_aria")}>
        {/* Nível de título (axe heading-order): h1 do topo -> h2 desta seção -> h3 de cada
            passo. Oculto na tela: o título visível do bloco é o de cada capítulo. */}
        <h2 className="sr-only">{t("inicio_narrativa_aria")}</h2>
        <div className="narrativa__passos">
          <nav className="narrativa__nav" aria-label={t("inicio_capitulos_aria")}>
            {capitulos.map((c, i) => (
              <button
                key={c.id}
                type="button"
                aria-current={i === passo ? "step" : undefined}
                onClick={() => setPasso(i)}
              >
                {c.periodo}
              </button>
            ))}
          </nav>
          <Passo
            cap={atual}
            i={passo}
            ativo
            resolvidos={resolvidosPorCap[`cap:${atual.id}`]}
            marcos={marcos}
          />
          <div className="narrativa__botoes">
            <button type="button" disabled={passo === 0} onClick={() => setPasso((p) => Math.max(0, p - 1))}>
              ← {t("inicio_anterior")}
            </button>
            <button
              type="button"
              disabled={passo === capitulos.length - 1}
              onClick={() => setPasso((p) => Math.min(capitulos.length - 1, p + 1))}
            >
              {t("inicio_proximo")} →
            </button>
          </div>
        </div>
        {mapa}
      </section>
    );
  }

  return (
    <section ref={secaoRef} className="narrativa" aria-label={t("inicio_narrativa_aria")}>
        {/* Nível de título (axe heading-order): h1 do topo -> h2 desta seção -> h3 de cada
            passo. Oculto na tela: o título visível do bloco é o de cada capítulo. */}
        <h2 className="sr-only">{t("inicio_narrativa_aria")}</h2>
      <div className="narrativa__passos">
        {capitulos.map((c, i) => (
          <Passo
            key={c.id}
            cap={c}
            i={i}
            ativo={i === passo}
            resolvidos={resolvidosPorCap[`cap:${c.id}`]}
            marcos={marcos}
            refPasso={(e) => {
              passosRef.current[i] = e;
            }}
            aoFocar={() => setPasso(i)}
          />
        ))}
      </div>
      {mapa}
    </section>
  );
}
