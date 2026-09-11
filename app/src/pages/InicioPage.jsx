// Página inicial (Fase 4b, B3): hero → "a história em N números" (KPIs com sparkline) →
// narrativa guiada com mapa fixo → cartões "Explore". Desenho portado de
// urban-canaa/web/src/tabs/Inicio.tsx; conteúdo de app/src/content/narrativa.json.
// Nenhum número é digitado aqui: todo valor é marcador resolvido por lib/marcadores.js
// contra data/processed/ e renderizado por ProvenanciaNumero; os cartões não têm número.
import { useEffect, useMemo, useState } from "react";
import narrativa from "../content/narrativa.json";
import { Kpi, Esqueleto, Erro } from "../components/ui.jsx";
import Narrativa from "../components/inicio/Narrativa.jsx";
import { TextoMarcado } from "../components/inicio/Marcador.jsx";
import { carregarFontesNarrativa, resolverNarrativa, resolverSerie } from "../lib/marcadores.js";
import { useI18n } from "../lib/i18n.jsx";

const SELO_CLASSE = { observado: "conforme", interpolado: "semdado", modelado: "atencao" };

const CARTOES = [
  { id: "mancha", rota: "/mancha" },
  { id: "provincia", rota: "/provincia" },
  { id: "populacao", rota: "/populacao" },
  { id: "graficos", rota: "/graficos" },
  { id: "artigo", rota: "/artigo" },
  { id: "metodologia", rota: "/metodologia" },
];

function porIdioma(obj, campo, lang) {
  return obj?.[`${campo}_${lang}`] ?? obj?.[`${campo}_pt`];
}

function useFontesNarrativa() {
  const [estado, setEstado] = useState({ fontes: null, erro: null });
  useEffect(() => {
    let vivo = true;
    carregarFontesNarrativa(narrativa)
      .then((fontes) => vivo && setEstado({ fontes, erro: null }))
      .catch((erro) => vivo && setEstado({ fontes: null, erro }));
    return () => {
      vivo = false;
    };
  }, []);
  return estado;
}

function KpiNarrativa({ kpi, resolvidos, fontes }) {
  const { t, lang } = useI18n();
  const serie = useMemo(() => (kpi.serie ? resolverSerie(kpi.serie, fontes) : null), [kpi, fontes]);
  useEffect(() => {
    if (serie?.erros.length) {
      (import.meta.env.DEV ? console.error : console.warn)(`[narrativa] série do KPI ${kpi.id}:`, serie.erros);
    }
  }, [serie, kpi.id]);
  const destaque = serie ? serie.anos.indexOf(kpi.destaque_ano) : -1;
  const selo = kpi.selo;
  return (
    <Kpi
      rotulo={<TextoMarcado molde={porIdioma(kpi, "rotulo", lang)} resolvidos={resolvidos} />}
      valor={<TextoMarcado molde={porIdioma(kpi, "valor", lang)} resolvidos={resolvidos} />}
      delta={<TextoMarcado molde={porIdioma(kpi, "delta", lang)} resolvidos={resolvidos} />}
      nota={
        <>
          {selo ? (
            <span className={`ard-pill ard-pill--${SELO_CLASSE[selo] ?? "semdado"} kpi__selo`}>
              {t(`inicio_selo_${selo}`)}
            </span>
          ) : null}{" "}
          <TextoMarcado molde={porIdioma(kpi, "nota", lang)} resolvidos={resolvidos} />
          {serie && serie.valores.filter((v) => v != null).length > 1 ? (
            <span className="sr-only">
              {" "}
              {t("inicio_sparkline_sr")
                .replace("{ini}", String(serie.anos[0]))
                .replace("{fim}", String(serie.anos[serie.anos.length - 1]))}
            </span>
          ) : null}
        </>
      }
      serie={serie ? serie.valores : undefined}
      destaque={destaque >= 0 ? destaque : undefined}
    />
  );
}

export default function InicioPage() {
  const { t, lang } = useI18n();
  const { fontes, erro } = useFontesNarrativa();
  const topo = narrativa.topo;

  const resolucao = useMemo(
    () => (fontes ? resolverNarrativa(narrativa, fontes, lang) : null),
    [fontes, lang]
  );

  // Falha de marcador é visível: erro no console em desenvolvimento (e na frase), aviso
  // em produção (traço na frase). O gancho de verificação só existe em desenvolvimento.
  useEffect(() => {
    if (!resolucao) return;
    if (resolucao.erros.length) {
      (import.meta.env.DEV ? console.error : console.warn)("[narrativa] marcadores não resolvidos:", resolucao.erros);
    }
    if (import.meta.env.DEV) {
      window.__narrativaResolucao = {
        total: resolucao.total,
        resolvidos: resolucao.resolvidos,
        erros: resolucao.erros,
      };
    }
  }, [resolucao]);

  const kpis = topo.kpis ?? [];

  return (
    <div className="inicio">
      <header className="inicio__hero">
        <p className="ard-kicker">{porIdioma(topo, "kicker", lang)}</p>
        <h1>{porIdioma(topo, "titulo", lang)}</h1>
        <p className="inicio__lead">
          {resolucao ? (
            <TextoMarcado molde={porIdioma(topo, "lead", lang)} resolvidos={resolucao.porBloco.topo} />
          ) : (
            porIdioma(topo, "lead", lang).replace(/\{\w+\}/g, "…")
          )}
        </p>
      </header>

      <section className="inicio__secao" aria-labelledby="inicio-numeros">
        <p className="ard-kicker" id="inicio-numeros">
          {t("inicio_numeros_kicker").replace("{n}", String(kpis.length))}
        </p>
        {erro ? (
          <Erro erro={erro} />
        ) : !resolucao ? (
          <Esqueleto altura={180} />
        ) : (
          <div className="kpis kpis--inicio">
            {kpis.map((k) => (
              <KpiNarrativa key={k.id} kpi={k} resolvidos={resolucao.porBloco[`kpi:${k.id}`]} fontes={fontes} />
            ))}
          </div>
        )}
      </section>

      {erro ? null : !resolucao ? (
        <Esqueleto altura={420} />
      ) : (
        <Narrativa capitulos={narrativa.capitulos} resolvidosPorCap={resolucao.porBloco} marcos={fontes.marcos} />
      )}

      <section className="inicio__secao" aria-labelledby="inicio-explore">
        <p className="ard-kicker">{t("inicio_explore_kicker")}</p>
        <h2 id="inicio-explore">{t("inicio_explore_titulo")}</h2>
        <div className="cartoes">
          {CARTOES.map((c) => (
            <a key={c.id} className="cartao ard-card" href={`#${c.rota}`}>
              <span className="cartao__titulo">{t(`inicio_cartao_${c.id}_titulo`)}</span>
              <span className="cartao__desc">{t(`inicio_cartao_${c.id}_desc`)}</span>
            </a>
          ))}
        </div>
      </section>
    </div>
  );
}
