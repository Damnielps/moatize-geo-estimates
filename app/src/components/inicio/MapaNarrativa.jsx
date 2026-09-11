// Mapa fixo da narrativa da página inicial (Fase 4b, B3). Desenho portado de
// urban-canaa/web/src/components/inicio/MapaNarrativa.tsx, com as diferenças que este
// estudo impõe:
// - SEM imagem de satélite: só os vetores classificados do `ano_mapa` do capítulo
//   (data/processed/app/imagery/), nas camadas que o capítulo declara em `camadas_mapa`;
// - troca de ano é CORTE discreto de fonte, nunca interpolação de geometria (ADR 0013);
// - `adensamento_2020_2025` só é desenhada quando o ano exibido é 2025 (regra de
//   lib/camadasBase.js, `camadaDisponivelNoAno`);
// - o "fantasma" é o contorno tracejado da camada `urbano` do `ano_fantasma`.
// Não interativo (`interactive: false`): a rolagem da página comanda o mapa, e o mapa
// não captura a roda do mouse nem o toque. Carregamento à prova de corrida com as MESMAS
// funções de MapaTemporal.jsx: dados só depois do `load`, resposta obsoleta descartada.
import { useEffect, useRef, useState } from "react";
import { Map as MapLibreMap, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { carregarGeojson, AOI_BBOX } from "../../lib/data.js";
import {
  CORES_CAMADA,
  CAMADAS_POR_ANO,
  COR_CONTORNO_FANTASMA,
  idsDaCamada,
  estiloAmostra,
  montarAtribuicao,
  camadaDisponivelNoAno,
  criarEstiloVazio,
  adicionarCamadaVarzea,
  adicionarCamadaAdensamento,
  adicionarContextoOsm,
  aplicarCamadasDoAno,
  mapaUtilizavel,
} from "../../lib/camadasBase.js";
import { useI18n } from "../../lib/i18n.jsx";

setWorkerUrl(`${import.meta.env.BASE_URL}vendor/maplibre/maplibre-gl-worker.mjs`);

const VAZIO = { type: "FeatureCollection", features: [] };
// Contexto fixo de leitura, igual em todos os passos: a água (o Zambeze) e a várzea (pedido
// do usuário, 2026-09-11), mais o contexto OSM do efeito próprio. Não é camada medida do
// capítulo; a legenda o marca como contexto e o enquadramento não o usa.
const CONTEXTO = ["agua", "varzea"];
const ESTATICAS = ["varzea", "adensamento_2020_2025"];

function reduzirMovimento() {
  return typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
}

// Envelope (lon/lat) das feições — enquadramento do passo lido do próprio dado, não
// digitado: o que o capítulo mostra define a janela.
function estenderBbox(bbox, gj) {
  const visitar = (c) => {
    if (typeof c[0] === "number") {
      if (c[0] < bbox[0]) bbox[0] = c[0];
      if (c[1] < bbox[1]) bbox[1] = c[1];
      if (c[0] > bbox[2]) bbox[2] = c[0];
      if (c[1] > bbox[3]) bbox[3] = c[1];
    } else c.forEach(visitar);
  };
  for (const f of gj?.features ?? []) if (f.geometry) visitar(f.geometry.coordinates);
  return bbox;
}

export default function MapaNarrativa({ ano, anoFantasma, camadas, rotulo }) {
  const { t } = useI18n();
  const containerRef = useRef(null);
  const marcadoresRef = useRef([]);
  const requisicaoRef = useRef(0);
  const [mapa, setMapa] = useState(null);
  // Aviso de carga: no primeiro acesso as camadas do passo levam alguns segundos, e um mapa
  // em branco sem aviso parece quebrado.
  const [carregando, setCarregando] = useState(true);

  // Cria o mapa uma vez; guarda a INSTÂNCIA só depois do `load` (ver MapaTemporal.jsx).
  useEffect(() => {
    let vivo = true;
    const map = new MapLibreMap({
      container: containerRef.current,
      style: criarEstiloVazio(),
      bounds: [
        [AOI_BBOX[0], AOI_BBOX[1]],
        [AOI_BBOX[2], AOI_BBOX[3]],
      ],
      fitBoundsOptions: { padding: 16 },
      interactive: false,
      attributionControl: false,
    });
    map.on("load", () => {
      if (!vivo) return;
      map.addSource("fantasma", { type: "geojson", data: VAZIO });
      // Fantasma: contorno tracejado escuro. Para que ele se leia também DENTRO da mancha
      // do ano exibido (o contorno do ano anterior cai quase todo dentro dela), o
      // preenchimento de `urbano` neste mapa é mais transparente que na aba Mancha.
      map.addLayer({
        id: "layer-fantasma",
        type: "line",
        source: "fantasma",
        paint: { "line-color": COR_CONTORNO_FANTASMA, "line-width": 1.1, "line-dasharray": [2, 1.5], "line-opacity": 0.9 },
      });
      setMapa(map);
    });
    if (import.meta.env.DEV) window.__teteMoatizeMapaNarrativa = map; // hook de verificação em dev
    return () => {
      vivo = false;
      setMapa(null);
      for (const { marker } of marcadoresRef.current) marker.remove();
      marcadoresRef.current = [];
      map.remove();
    };
  }, []);

  // Atribuição no idioma corrente (PT/EN), refeita na troca de idioma. Recolhida no botão
  // (i) quando o mapa é estreito: o mapa não é interativo, então o MapLibre nunca a
  // recolheria sozinho (recolhe no primeiro arrasto).
  useEffect(() => {
    if (!mapa) return;
    const remover = montarAtribuicao(mapa, t("mapa_atribuicao"));
    containerRef.current
      ?.querySelector(".maplibregl-ctrl-attrib.maplibregl-compact")
      ?.classList.remove("maplibregl-compact-show");
    return remover;
  }, [mapa, t]);

  // Contexto OSM estático, visível desde o primeiro passo (pedido do usuário, 2026-09-11):
  // rodovias, ferrovia do Sena e aeródromo de Tete, mais os topônimos de cidade e vila. Não
  // entra no enquadramento (que só usa as camadas do ano e o fantasma).
  useEffect(() => {
    if (!mapa) return;
    let cancelado = false;
    const ativas = { osm_lugares: true, osm_vias: true, osm_ferrovia: true, osm_aerodromo: true };
    adicionarContextoOsm(mapa, () => ativas, () => cancelado)
      .then((marcadores) => {
        if (!marcadores) return;
        marcadoresRef.current = marcadores;
        for (const { marker, place } of marcadores) {
          marker.getElement().style.display = place === "city" || place === "town" ? "" : "none";
        }
      })
      .catch((e) => {
        if (vigente()) setCarregando(false);
        if (!cancelado) console.error(e);
      });
    return () => {
      cancelado = true;
    };
  }, [mapa]);

  // Estado do passo: camadas do ano, estáticas, fantasma, visibilidade e enquadramento
  // aplicados JUNTOS, e só se esta ainda for a requisição mais recente.
  const chaveCamadas = camadas.join(",");
  useEffect(() => {
    if (!mapa) return;
    const minha = ++requisicaoRef.current;
    let cancelado = false;
    const vigente = () => !cancelado && minha === requisicaoRef.current;
    setCarregando(true);
    const ativas = new Set([...camadas, ...CONTEXTO]);
    const visivel = (c) => ativas.has(c) && camadaDisponivelNoAno(c, ano);

    // Estáticas (várzea, adensamento): adicionadas à parte, uma vez por mapa, com a
    // visibilidade lida quando chegam. NÃO entram no Promise.all do passo — não podem
    // atrasar a aplicação das camadas do capítulo.
    const falha = (e) => {
      if (!cancelado) console.error(e);
    };
    adicionarCamadaVarzea(mapa, () => visivel("varzea"), () => !vigente()).catch(falha);
    adicionarCamadaAdensamento(mapa, () => visivel("adensamento_2020_2025"), () => !vigente()).catch(falha);

    // Causa-raiz da corrida da montagem inicial (B6): este Promise.all pedia as SEIS classes
    // do ano (inclusive cultivo irrigado e sequeiro, 2–6 MB por ano, que a home nunca
    // mostra) e ainda a várzea (2,6 MB) e o adensamento. Nada do passo era aplicado — nem
    // camadas, nem fantasma, nem enquadramento — até o arquivo mais pesado chegar e ser lido;
    // na primeira visita o mapa ficava só com os topônimos (Marker de DOM, do efeito de
    // contexto). Voltar ao passo desenhava porque o cache já estava quente. Agora o passo
    // pede só as classes que mostra (+ água), e as estáticas correm à parte.
    const doAno = CAMADAS_POR_ANO.filter((c) => ativas.has(c));
    Promise.all([
      aplicarCamadasDoAno(mapa, ano, visivel, vigente, doAno),
      anoFantasma != null ? carregarGeojson("urbano", anoFantasma) : Promise.resolve(VAZIO),
      // A várzea é contexto estático (a mesma em todos os anos): desenhada em todo passo,
      // mas fora do enquadramento — senão o zoom abriria para a planície inteira do Zambeze
      // e o capítulo perderia o foco em Tete e Moatize.
      Promise.all(camadas.filter((c) => c !== "varzea" && camadaDisponivelNoAno(c, ano)).map((c) =>
        c === "adensamento_2020_2025" ? carregarGeojson(c, null) : carregarGeojson(c, ano)
      )),
    ])
      .then(([aplicou, gjFantasma, gjsPasso]) => {
        if (vigente()) setCarregando(false);
        if (!aplicou || !vigente() || !mapaUtilizavel(mapa)) return;
        mapa.getSource("fantasma")?.setData(gjFantasma ?? VAZIO);
        for (const c of [...CAMADAS_POR_ANO, ...ESTATICAS]) {
          for (const id of idsDaCamada(c)) {
            if (mapa.getLayer(id)) mapa.setLayoutProperty(id, "visibility", visivel(c) ? "visible" : "none");
          }
        }
        if (mapa.getLayer("layer-urbano")) mapa.setPaintProperty("layer-urbano", "fill-opacity", 0.5);
        if (mapa.getLayer("layer-fantasma")) mapa.moveLayer("layer-fantasma");
        const bbox = [Infinity, Infinity, -Infinity, -Infinity];
        for (const g of gjsPasso) estenderBbox(bbox, g);
        estenderBbox(bbox, gjFantasma);
        const valido = bbox.every(Number.isFinite) && bbox[2] > bbox[0] && bbox[3] > bbox[1];
        const alvo = valido
          ? [[bbox[0], bbox[1]], [bbox[2], bbox[3]]]
          : [[AOI_BBOX[0], AOI_BBOX[1]], [AOI_BBOX[2], AOI_BBOX[3]]];
        const semMovimento = reduzirMovimento();
        // Em tela estreita o selo cobre a faixa de cima do mapa: o enquadramento desconta
        // a altura dele, para nenhuma feição do capítulo ficar escondida sob a legenda.
        const selo = containerRef.current?.parentElement?.querySelector(".narrativa__selo");
        const largura = containerRef.current?.clientWidth ?? 0;
        const topo = selo && largura && selo.offsetWidth > largura / 2 ? selo.offsetHeight + 20 : 28;
        mapa.fitBounds(alvo, {
          padding: { top: topo, bottom: 28, left: 28, right: 28 },
          duration: semMovimento ? 0 : 900,
          animate: !semMovimento,
          essential: false,
        });
      })
      .catch((e) => {
        if (!cancelado) console.error(e);
      });
    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapa, ano, anoFantasma, chaveCamadas]);

  // O contêiner muda de tamanho entre layouts (≤ 900 px); o MapLibre precisa saber.
  useEffect(() => {
    if (!mapa || typeof ResizeObserver === "undefined") return;
    const ro = new ResizeObserver(() => mapa.resize());
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [mapa]);

  const legenda = camadas.filter((c) => camadaDisponivelNoAno(c, ano));

  return (
    <div className="narrativa__mapa" role="figure" aria-label={rotulo}>
      <div ref={containerRef} className="narrativa__canvas" />
      <div className="narrativa__selo" aria-hidden="true">
        <span className="narrativa__ano">{ano}</span>
        {carregando ? <span className="narrativa__carregando">{t("inicio_mapa_carregando")}</span> : null}
        <ul className="narrativa__legenda">
          {legenda.map((c) => (
            <li key={c}>
              <i className="narrativa__amostra" style={estiloAmostra(c)} />
              {t(`inicio_legenda_${c}`)}
            </li>
          ))}
          {anoFantasma != null && (
            <li>
              <i className="narrativa__amostra narrativa__amostra--linha" style={{ borderTopColor: COR_CONTORNO_FANTASMA }} />
              {t("inicio_legenda_fantasma").replace("{ano}", String(anoFantasma))}
            </li>
          )}
          <li className="narrativa__legenda-contexto">
            <i className="narrativa__amostra" style={estiloAmostra("agua")} />
            {t("inicio_legenda_agua")}
          </li>
          <li className="narrativa__legenda-contexto">
            <i className="narrativa__amostra narrativa__amostra--via" style={{ borderTopColor: CORES_CAMADA.osm_vias }} />
            {t("inicio_legenda_vias")}
          </li>
          <li className="narrativa__legenda-contexto">
            <i className="narrativa__amostra narrativa__amostra--ferrovia" style={{ borderTopColor: CORES_CAMADA.osm_ferrovia }} />
            {t("inicio_legenda_ferrovia")}
          </li>
          <li className="narrativa__legenda-contexto">
            <i className="narrativa__amostra" style={estiloAmostra("osm_aerodromo")} />
            {t("inicio_legenda_aerodromo")}
          </li>
        </ul>
      </div>
    </div>
  );
}
