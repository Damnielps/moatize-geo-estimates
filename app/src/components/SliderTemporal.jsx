// Linha do tempo do mapa (§6, ADR 0013): controles ‹ ▶ ›, trilha com fases sombreadas,
// marcas de censo e de marcos pontuais, âncoras de imagem como ticks mais fortes.
// Porte do DESENHO de urban-canaa/web/src/components/mapa/Slider.tsx (TS + ECharts)
// para JSX puro — sem ECharts, sem nova dependência.
import { useCallback, useEffect, useMemo, useRef } from "react";
import { useStore } from "../lib/store.jsx";
import { useMarcos } from "../lib/marcos.js";
import { useI18n } from "../lib/i18n.jsx";

const AGUARDA_MS = 1200;
// Domínio de exibição da trilha: começa em 1997 (censo mais antigo) e termina na
// última âncora de imagem (2025). O censo previsto de 2027 cai fora deste domínio de
// propósito — para caber 1997 sem esticar a trilha até 2027 — e é indicado por uma
// seta na borda direita, não por uma posição proporcional inexistente.
const DOMINIO_MIN = 1997;

function prefereReduzirMovimento() {
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

function indiceMaisProximo(anos, ano) {
  let melhor = 0;
  let menorDist = Infinity;
  anos.forEach((a, i) => {
    const d = Math.abs(a - ano);
    if (d < menorDist) {
      menorDist = d;
      melhor = i;
    }
  });
  return melhor;
}

function TipoMarcoRotulo({ tipo }) {
  const { t } = useI18n();
  const chave = `marco_tipo_${tipo}`;
  const rotulo = t(chave);
  return rotulo === chave ? tipo : rotulo;
}

function NivelPalavra({ nivel }) {
  const { t } = useI18n();
  if (nivel === "secundario") return t("slider_nivel_secundario");
  if (nivel === "C") return t("slider_nivel_c");
  return null;
}

/** Uma marca posicionada na trilha (censo ou marco pontual), com tooltip sob foco/hover. */
function Marca({ marco, pct, variante, foraDoDominio, onSelecionar }) {
  const { t, lang } = useI18n();
  const vazado = marco.nivel === "secundario" || marco.nivel === "C";
  const nivelTexto = <NivelPalavra nivel={marco.nivel} />;
  const dataExibida = marco.ano_fim
    ? `${marco.inicio}${marco.fim ? `–${marco.fim}` : ""}`
    : String(marco.inicio);

  // Não é mais descendente do elemento `role="slider"` (ver comentário em
  // SliderTemporal.jsx), então um clique aqui não borbulha mais até `clicarTrilha` —
  // chama `onSelecionar` diretamente para preservar o mesmo comportamento de antes
  // (clicar numa marca de censo/marco leva ao ano-âncora mais próximo daquela data).
  return (
    <span
      className={
        "slider-temporal__marca " +
        `slider-temporal__marca--${variante}` +
        (vazado ? " slider-temporal__marca--vazado" : "") +
        (foraDoDominio ? " slider-temporal__marca--fora" : "")
      }
      style={foraDoDominio ? undefined : { left: `${pct}%` }}
      tabIndex={0}
      role="button"
      aria-label={marco.rotulo}
      onClick={onSelecionar}
    >
      {foraDoDominio ? <span className="slider-temporal__seta" aria-hidden="true">→</span> : null}
      <span role="tooltip" className="slider-temporal__tooltip">
        <strong>{marco.rotulo}</strong>
        {variante === "marco" ? (
          <span className="slider-temporal__tooltip-tipo">
            {" "}
            (<TipoMarcoRotulo tipo={marco.tipo} />)
          </span>
        ) : null}
        <br />
        {dataExibida}
        {foraDoDominio ? ` — ${t("slider_fora_do_intervalo")}` : ""}
        <br />
        {t("fonte")}: {marco.fonte ?? (lang === "pt" ? "não disponível" : "not available")}
        {nivelTexto ? (
          <>
            {" · "}
            <span className="slider-temporal__tooltip-nivel">{nivelTexto}</span>
          </>
        ) : (
          <>
            {" · "}
            {t("nivel")}: {marco.nivel}
          </>
        )}
        {marco.nota ? <span className="slider-temporal__tooltip-nota"><br />{marco.nota}</span> : null}
      </span>
    </span>
  );
}

// Ícones em SVG (não caracteres ‹ ▶ ›): glifos de texto centralizam de modo diferente em
// cada fonte e deformavam os botões circulares. `currentColor` herda a cor do botão.
function Icone({ tipo }) {
  const d = {
    anterior: "M14.5 5.5 8 12l6.5 6.5",
    proximo: "M9.5 5.5 16 12l-6.5 6.5",
  }[tipo];
  if (tipo === "play") {
    return (
      <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" focusable="false">
        <path d="M8 5.5v13l10.5-6.5z" fill="currentColor" />
      </svg>
    );
  }
  if (tipo === "pausa") {
    return (
      <svg viewBox="0 0 24 24" width="14" height="14" aria-hidden="true" focusable="false">
        <rect x="7" y="5.5" width="3.6" height="13" rx="1" fill="currentColor" />
        <rect x="13.4" y="5.5" width="3.6" height="13" rx="1" fill="currentColor" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true" focusable="false">
      <path d={d} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export default function SliderTemporal() {
  const { ano, setAno, anosDisponiveis, tocando, setTocando } = useStore();
  const { fases, pontuais, censos, carregando } = useMarcos();
  const { t } = useI18n();
  const trilhaRef = useRef(null);

  const dominioMax = anosDisponiveis[anosDisponiveis.length - 1];
  const dominioMin = DOMINIO_MIN;
  const total = dominioMax - dominioMin;
  const indiceAtual = useMemo(
    () => anosDisponiveis.indexOf(ano),
    [anosDisponiveis, ano]
  );

  const pct = useCallback(
    (a) => {
      const clamped = Math.min(dominioMax, Math.max(dominioMin, a));
      return ((clamped - dominioMin) / total) * 100;
    },
    [dominioMin, dominioMax, total]
  );

  function irParaIndice(i) {
    const clamped = Math.min(anosDisponiveis.length - 1, Math.max(0, i));
    setAno(anosDisponiveis[clamped]);
  }

  const alternarPlay = useCallback(() => {
    if (prefereReduzirMovimento()) return; // botão avisa via title; não inicia autoplay
    setTocando((tAtual) => {
      if (tAtual) return false;
      if (indiceAtual >= anosDisponiveis.length - 1) {
        setAno(anosDisponiveis[0]);
      }
      return true;
    });
  }, [indiceAtual, anosDisponiveis, setAno, setTocando]);

  // Reprodução: avança POR ÍNDICE de âncora a cada 1200 ms; para em 2025 (último índice).
  useEffect(() => {
    if (!tocando) return;
    if (prefereReduzirMovimento()) {
      setTocando(false);
      return;
    }
    if (indiceAtual >= anosDisponiveis.length - 1) {
      setTocando(false);
      return;
    }
    const id = window.setTimeout(() => {
      irParaIndice(indiceAtual + 1);
    }, AGUARDA_MS);
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tocando, indiceAtual, anosDisponiveis]);

  function teclado(e) {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      irParaIndice(indiceAtual + 1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      irParaIndice(indiceAtual - 1);
    } else if (e.key === "Home") {
      e.preventDefault();
      irParaIndice(0);
    } else if (e.key === "End") {
      e.preventDefault();
      irParaIndice(anosDisponiveis.length - 1);
    } else if (e.key === " ") {
      e.preventDefault();
      alternarPlay();
    }
  }

  function clicarTrilha(e) {
    const el = trilhaRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const p = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
    const anoClicado = dominioMin + p * total;
    const indice = indiceMaisProximo(anosDisponiveis, anoClicado);
    irParaIndice(indice);
  }

  const faseAtual = fases.find((f) => ano >= f.ano_inicio && ano < f.ano_fim);

  const reduzido = prefereReduzirMovimento();

  return (
    <div className="slider-temporal">
      <div className="slider-temporal__controles">
        <button
          type="button"
          className="botao-icone"
          onClick={() => irParaIndice(indiceAtual - 1)}
          disabled={indiceAtual <= 0}
          aria-label={t("slider_ano_anterior")}
        >
          <Icone tipo="anterior" />
        </button>
        <button
          type="button"
          className="botao-icone slider-temporal__play"
          onClick={alternarPlay}
          aria-pressed={tocando}
          aria-label={tocando ? t("slider_pausar") : t("slider_reproduzir")}
          title={reduzido ? t("slider_movimento_reduzido") : undefined}
        >
          <Icone tipo={tocando ? "pausa" : "play"} />
        </button>
        <button
          type="button"
          className="botao-icone"
          onClick={() => irParaIndice(indiceAtual + 1)}
          disabled={indiceAtual >= anosDisponiveis.length - 1}
          aria-label={t("slider_proximo_ano")}
        >
          <Icone tipo="proximo" />
        </button>
        <span className="slider-temporal__ano">{ano}</span>
        {faseAtual ? <span className="slider-temporal__fase-atual">{faseAtual.rotulo}</span> : null}
        {reduzido ? <span className="slider-temporal__aviso-movimento">{t("slider_movimento_reduzido")}</span> : null}
      </div>

      {/* `.slider-temporal__trilha-wrap` é só o contêiner de posicionamento: o widget
          `role="slider"` fica isolado em `.slider-temporal__trilha`, sem descendentes
          focáveis (fases/trilho/ticks/alça são decorativos). As marcas de censo/marco
          (cada uma `role="button"` com tooltip própria) são desenhadas como IRMÃS, não
          filhas, do elemento `role="slider"` — nested-interactive (axe, Fase 4b B5):
          um `role="button"` focável dentro de um widget `role="slider"` confundia
          leitores de tela sobre qual é o controle. Mesmas coordenadas (mesmo `pct`,
          mesma largura via CSS), então a posição visual não muda. */}
      <div className="slider-temporal__trilha-wrap">
        <div
          ref={trilhaRef}
          className="slider-temporal__trilha"
          role="slider"
          tabIndex={0}
          aria-label={t("slider_aria_label")}
          aria-valuemin={dominioMin}
          aria-valuemax={dominioMax}
          aria-valuenow={ano}
          aria-valuetext={String(ano)}
          onKeyDown={teclado}
          onClick={clicarTrilha}
        >
          {fases.map((f) => {
            const esquerda = pct(f.ano_inicio);
            const direita = pct(f.ano_fim);
            const largura = direita - esquerda;
            if (largura <= 0) return null;
            const ativa = faseAtual?.id === f.id;
            return (
              <span
                key={f.id}
                className={"slider-temporal__fase" + (ativa ? " slider-temporal__fase--ativa" : "")}
                style={{ left: `${esquerda}%`, width: `${largura}%` }}
                title={f.rotulo}
              />
            );
          })}

          <span className="slider-temporal__trilho" />
          <span className="slider-temporal__preenchido" style={{ width: `${pct(ano)}%` }} />

          {anosDisponiveis.map((a) => (
            <span
              key={a}
              className="slider-temporal__tick slider-temporal__tick--ancora"
              style={{ left: `${pct(a)}%` }}
            />
          ))}

          <span className="slider-temporal__alca" style={{ left: `${pct(ano)}%` }} />
        </div>

        {!carregando &&
          censos.map((c) => {
            const foraDoDominio = c.ano_inicio > dominioMax + 0.001;
            return (
              <Marca
                key={c.id}
                marco={c}
                pct={foraDoDominio ? 100 : pct(c.ano_inicio)}
                variante="censo"
                foraDoDominio={foraDoDominio}
                onSelecionar={
                  foraDoDominio
                    ? undefined
                    : () => irParaIndice(indiceMaisProximo(anosDisponiveis, c.ano_inicio))
                }
              />
            );
          })}

        {!carregando &&
          pontuais.map((m) => {
            const foraDoDominio = m.ano_inicio > dominioMax + 0.001;
            if (foraDoDominio) return null; // fora de escopo desta trilha; só censos usam a seta
            return (
              <Marca
                key={m.id}
                marco={m}
                pct={pct(m.ano_inicio)}
                variante="marco"
                foraDoDominio={false}
                onSelecionar={() => irParaIndice(indiceMaisProximo(anosDisponiveis, m.ano_inicio))}
              />
            );
          })}
      </div>

      <div className="slider-temporal__eixo" aria-hidden="true">
        <span className="slider-temporal__rot" style={{ left: 0 }}>
          {dominioMin}
        </span>
        {anosDisponiveis.slice(1, -1).map((a) => (
          <span key={a} className="slider-temporal__rot slider-temporal__rot--ancora" style={{ left: `${pct(a)}%` }}>
            {a}
          </span>
        ))}
        <span className="slider-temporal__rot" style={{ right: 0 }}>
          {dominioMax}
        </span>
      </div>
    </div>
  );
}
