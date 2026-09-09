import { useState } from "react";
import MapaTemporal from "../components/MapaTemporal.jsx";
import { useStore } from "../lib/store.jsx";
import { useI18n } from "../lib/i18n.jsx";

const CAPITULOS = [
  {
    id: "base",
    ano: 2000,
    titulo_pt: "Linha de base (1997–2005)",
    titulo_en: "Baseline (1997–2005)",
    texto_pt:
      "Antes da concessão à Vale (licitação 2004, licença 2006), a mancha construída de Tete e Moatize cresce a ritmo pré-boom. Este é o contrafactual de comparação para todo o resto da periodização — e o único ponto em que os placebos temporais (P2) fazem sentido.",
    texto_en:
      "Before the Vale concession (2004 bid, 2006 license), the built-up footprint of Tete and Moatize grows at pre-boom pace. This is the comparison counterfactual for the rest of the periodization.",
  },
  {
    id: "implantacao",
    ano: 2010,
    titulo_pt: "Implantação (2005–2011)",
    titulo_en: "Implementation (2005–2011)",
    texto_pt:
      "Obras a partir de ~2007; reassentamento de Cateme e 25 de Setembro entre nov/2009 e abr/2010. A pegada industrial ainda é pequena; a pegada de reassentamento aparece pela primeira vez, fora da mancha urbana orgânica.",
    texto_en:
      "Works from ~2007; Cateme and 25 de Setembro resettlement between Nov/2009 and Apr/2010. The industrial footprint is still small; the resettlement footprint appears for the first time, outside the organic urban footprint.",
  },
  {
    id: "boom",
    ano: 2015,
    titulo_pt: "Boom (2011–2015)",
    titulo_en: "Boom (2011–2015)",
    texto_pt:
      "Operação da Vale desde maio de 2011; Benga (Riversdale/Rio Tinto) desde 2012. Pico de preços do carvão. A pegada industrial cresce em direção aos ~59 km² medidos por Maus et al. (2017–2019). O ITS testado em 2011 (S_WSF_taxa) tem veredito FALHA no placebo — não sustentado como quebra causal isolada.",
    texto_en:
      "Vale operating since May 2011; Benga (Riversdale/Rio Tinto) since 2012. Coal price peak. The industrial footprint grows toward the ~59 km² measured by Maus et al. (2017–2019). The 2011 ITS break fails its placebo test.",
  },
  {
    id: "bust",
    ano: 2020,
    titulo_pt: "Bust e ajuste (2015–2019)",
    titulo_en: "Bust and adjustment (2015–2019)",
    texto_pt:
      "Queda dos preços do carvão (2015–2016); Corredor de Nacala (2017). A quebra de 2016 na série de luz harmonizada (B_luz_HARM) tem veredito CONTRAFACTUAL NÃO SUSTENTADO (peso de controle sintético concentrado em >80% num único doador; rank fora do top-2 no placebo espacial).",
    texto_en:
      "Coal price drop (2015–2016); Nacala Corridor (2017). The 2016 break in the harmonized night-light series has an UNSUPPORTED counterfactual verdict.",
  },
  {
    id: "transicao",
    ano: 2025,
    titulo_pt: "Transição (2019–2025)",
    titulo_en: "Transition (2019–2025)",
    texto_pt:
      "Saída da Vale do negócio de carvão (venda à Vulcan Minerals, 2022 — situação a reverificar). A quebra de 2022 também tem veredito CONTRAFACTUAL NÃO SUSTENTADO, e a queda observada nesse ano NÃO pode ser atribuída à mina (ADR 0015, decisão 4): a decomposição por camada não é partição: a razão teto/piso tem mediana de 2,1 (industrial), 1,8 (urbano) e 5,2 (reassentamento), e chega a 6,7 no pior ano. Só o sinal comum às duas envoltórias é afirmável, nunca um valor único.",
    texto_en:
      "Vale's exit from the coal business (sale to Vulcan Minerals, 2022 — status to re-verify). The 2022 break also has an UNSUPPORTED counterfactual verdict, and the observed drop that year CANNOT be attributed to the mine (ADR 0015).",
  },
];

export default function NarrativaPage() {
  const { camadasAtivas } = useStore();
  const { lang, t } = useI18n();
  const [passo, setPasso] = useState(0);
  const cap = CAPITULOS[passo];

  return (
    <div>
      <h2>{t("nav_narrativa")}</h2>
      <nav className="narrativa-nav" aria-label="Capítulos da narrativa">
        {CAPITULOS.map((c, i) => (
          <button
            key={c.id}
            type="button"
            aria-current={i === passo ? "step" : undefined}
            onClick={() => setPasso(i)}
          >
            {c.ano}
          </button>
        ))}
      </nav>

      <div className="mapa-layout" style={{ gridTemplateColumns: "1fr 380px" }}>
        <div className="mapa-coluna-principal">
          <MapaTemporal ano={cap.ano} camadasAtivas={camadasAtivas} />
        </div>
        <article className="narrativa-capitulo">
          <p className="ard-kicker">{cap.ano}</p>
          <h3>{lang === "pt" ? cap.titulo_pt : cap.titulo_en}</h3>
          <p>{lang === "pt" ? cap.texto_pt : cap.texto_en}</p>
          <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
            <button type="button" disabled={passo === 0} onClick={() => setPasso((p) => Math.max(0, p - 1))}>
              ← {lang === "pt" ? "anterior" : "previous"}
            </button>
            <button type="button" disabled={passo === CAPITULOS.length - 1} onClick={() => setPasso((p) => Math.min(CAPITULOS.length - 1, p + 1))}>
              {lang === "pt" ? "próximo" : "next"} →
            </button>
          </div>
        </article>
      </div>
    </div>
  );
}
