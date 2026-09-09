import { useEffect, useRef, useState } from "react";
import {
  Map as MapLibreMap,
  Marker,
  NavigationControl,
  AttributionControl,
  setWorkerUrl,
} from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
// URL do worker resolvida pelo empacotador, não pelo MapLibre.
//
// Sem isto, o MapLibre monta a URL sozinho: `new URL("./maplibre-gl-worker.mjs",
// import.meta.url)`. No build de produção `import.meta.url` é `/assets/index-<hash>.js`,
// então a URL vira `/assets/maplibre-gl-worker.mjs` — arquivo que o Vite nunca emite. O
// worker responde 404, MORRE EM SILÊNCIO (nenhuma exceção, nenhum evento `error`), e o
// mapa pinta só o fundo: `isSourceLoaded()` fica `false` para sempre em TODAS as fontes
// e `queryRenderedFeatures()` devolve zero. Em dev o arquivo existe, mas o Vite lhe
// injeta `import "/@vite/client"`, que quebra dentro de um Worker — mesmo sintoma.
// `?url` sozinho tambem nao serve: copia o worker verbatim, e ele importa
// `./maplibre-gl-shared.mjs` por caminho relativo, que o Vite emite com hash e outro
// nome. Os dois arquivos vao para `public/vendor/maplibre/` por
// `scripts/sync-maplibre-worker.mjs` (pre-dev e pre-build), com os nomes originais e
// lado a lado — caminho fixo, identico em dev e em producao.
import { carregarGeojson, carregarJson, AOI_BBOX } from "../lib/data.js";

setWorkerUrl(`${import.meta.env.BASE_URL}vendor/maplibre/maplibre-gl-worker.mjs`);

// Cores do Sistema Ardósia (viz-*) — nunca cor arbitrária fora do token.
export const CORES_CAMADA = {
  urbano: "#24404F", // viz-1
  industrial: "#9C5B41", // viz-2
  reassentamento: "#6E3B45", // viz-6
  cultivo_irrigado: "#3D5A4C", // viz-3
  cultivo_sequeiro: "#A98A3F", // viz-5 (âmbar — "candidata, não confirmada")
  agua: "#7E9BAA", // viz-4
  varzea: "#A7BFB4", // viz-div-6
  osm_vias: "#5B6B73", // contexto — malha viária (OSM)
  osm_ferrovia: "#24404F", // contexto — ferrovia do Sena (OSM)
  osm_aerodromo: "#6E3B45", // contexto — aeródromo de Tete/Chingodzi (OSM)
  osm_lugares: "#9C5B41", // contexto — topônimos (OSM), terracota de destaque
  // Camada modelada `adensamento_2020_2025` (ADR 0016): categórica por `classe`,
  // não contínua. `adensando` e `expansao_nova` em destaque (terracota/âmbar);
  // `consolidado`/`esparso_estavel`/`pegada_industrial` em tons neutros. A classe
  // `vazio_estavel` não está no vetor publicado (ADR 0016 §Decisão-6) — sem cor aqui.
  adensamento_2020_2025: "#9C5B41", // cor representativa p/ swatch da legenda = adensando
  adensamento_adensando: "#9C5B41", // viz-2, destaque
  adensamento_expansao_nova: "#A98A3F", // viz-5, destaque
  adensamento_consolidado: "#A9BEC9", // viz-seq-2, neutro
  adensamento_esparso_estavel: "#D8D4CC", // viz-div-4, neutro
  adensamento_pegada_industrial: "#C08066", // viz-div-2, distinto de `industrial` (viz-2)
};

// Classifica um `place` do OSM em uma classe de tamanho de rótulo (city > town >
// village > suburb/hamlet), conforme a tarefa de contexto (topônimos/vias/ferrovia).
function classeDeLugar(place) {
  if (place === "city") return "city";
  if (place === "town") return "town";
  if (place === "village") return "village";
  return "pequeno"; // suburb, neighbourhood, hamlet, etc.
}

// Mapa de nome de camada (chave de `camadasAtivas`) para id de layer MapLibre — a
// maioria segue o padrão `layer-<camada>`, mas `varzea` e as duas camadas de contexto
// que usam travessão em vez de sublinhado no id têm de ser mapeadas explicitamente.
const ID_LAYER_POR_CAMADA = {
  varzea: "varzea-fill",
  osm_vias: "layer-osm-vias",
  osm_ferrovia: "layer-osm-ferrovia",
  osm_aerodromo: "layer-osm-aerodromo-area",
};

const ESTILO_VAZIO = {
  version: 8,
  // `glyphs` é OMITIDO, não definido como undefined. O validador de estilo do MapLibre
  // trata a chave presente-com-undefined como valor inválido ("glyphs: string expected,
  // undefined found") e o erro impede o evento `load` de disparar — nenhuma camada é
  // adicionada e o mapa fica em branco, sem erro visível na tela.
  // Sem `glyphs` não há rótulo de texto, o que é intencional: este estilo não tem
  // camada `symbol`.
  sources: {},
  layers: [
    { id: "fundo", type: "background", paint: { "background-color": "#E3E9EC" } },
  ],
};

/**
 * Mapa MapLibre sem dependência de tile de terceiros (sem chave de API, sem serviço
 * externo): só as camadas GeoJSON de data/processed/app/imagery/. Troca de ano é corte
 * discreto de fonte de dado — NUNCA interpolação de geometria (DECISOES.md item 7,
 * ADR 0013: churn de 31-54% entre anos consecutivos tornaria uma transição suave uma
 * mentira animada de "movimento" que não existe no dado).
 */

export default function MapaTemporal({ ano, camadasAtivas, onManifest }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const marcadoresRef = useRef([]); // { marker, place } — topônimos (DOM, sem symbol/glyphs)
  const camadasAtivasRef = useRef(camadasAtivas);
  const [pronto, setPronto] = useState(false);

  camadasAtivasRef.current = camadasAtivas;

  // Aplica visibilidade dos rótulos de topônimo combinando dois critérios independentes:
  // o toggle "osm_lugares" do painel de camadas e o zoom atual (classes pequenas —
  // suburb/hamlet/neighbourhood — ficam ilegíveis e sobrepostas em zoom baixo).
  function aplicarVisibilidadeRotulos() {
    const map = mapRef.current;
    if (!map) return;
    const ligado = !!camadasAtivasRef.current.osm_lugares;
    const zoom = map.getZoom();
    for (const { marker, place } of marcadoresRef.current) {
      const pequeno = place === "pequeno";
      const visivel = ligado && !(pequeno && zoom < 10);
      marker.getElement().style.display = visivel ? "" : "none";
    }
  }

  useEffect(() => {
    const map = new MapLibreMap({
      container: containerRef.current,
      style: ESTILO_VAZIO,
      bounds: [
        [AOI_BBOX[0], AOI_BBOX[1]],
        [AOI_BBOX[2], AOI_BBOX[3]],
      ],
      fitBoundsOptions: { padding: 20 },
      attributionControl: false,
    });
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    map.addControl(
      new AttributionControl({
        customAttribution:
          "Tete–Moatize · classificação própria (Landsat/Sentinel-2) · data/processed/ · " +
          "vias, ferrovia e topônimos: © OpenStreetMap contributors (ODbL)",
      })
    );
    map.on("load", () => setPronto(true));
    map.on("zoom", aplicarVisibilidadeRotulos);
    mapRef.current = map;
    if (import.meta.env.DEV) window.__teteMoatizeMap = map; // hook de verificação em dev
    carregarJson("imagery/manifest.json").then((m) => onManifest?.(m));
    return () => {
      for (const { marker } of marcadoresRef.current) marker.remove();
      marcadoresRef.current = [];
      map.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Camada estática (várzea) — carregada uma vez.
  useEffect(() => {
    if (!pronto) return;
    const map = mapRef.current;
    let cancelado = false;
    carregarGeojson("varzea", null).then((gj) => {
      if (cancelado || map.getSource("varzea")) return;
      map.addSource("varzea", { type: "geojson", data: gj });
      map.addLayer({
        id: "varzea-fill",
        type: "fill",
        source: "varzea",
        layout: { visibility: camadasAtivas.varzea ? "visible" : "none" },
        paint: { "fill-color": CORES_CAMADA.varzea, "fill-opacity": 0.35 },
      });
    });
    return () => {
      cancelado = true;
    };
  }, [pronto]); // eslint-disable-line react-hooks/exhaustive-deps

  // Camada `adensamento_2020_2025` (ADR 0016) — carregada uma vez, SEM sufixo de ano
  // (`carregarGeojson("adensamento_2020_2025", null)`): é uma síntese única do
  // intervalo 2020→2025, não uma série por ano-âncora. Categórica por `classe`
  // (`fill-color` por `match`), desligada por padrão (store.jsx) para não competir
  // com as camadas observadas na primeira tela.
  useEffect(() => {
    if (!pronto) return;
    const map = mapRef.current;
    let cancelado = false;
    carregarGeojson("adensamento_2020_2025", null).then((gj) => {
      if (cancelado || map.getSource("adensamento_2020_2025")) return;
      map.addSource("adensamento_2020_2025", { type: "geojson", data: gj });
      map.addLayer({
        id: "layer-adensamento_2020_2025",
        type: "fill",
        source: "adensamento_2020_2025",
        layout: { visibility: camadasAtivas.adensamento_2020_2025 ? "visible" : "none" },
        paint: {
          "fill-color": [
            "match",
            ["get", "classe"],
            "adensando", CORES_CAMADA.adensamento_adensando,
            "expansao_nova", CORES_CAMADA.adensamento_expansao_nova,
            "consolidado", CORES_CAMADA.adensamento_consolidado,
            "esparso_estavel", CORES_CAMADA.adensamento_esparso_estavel,
            "pegada_industrial", CORES_CAMADA.adensamento_pegada_industrial,
            "#B4B2A9", // fallback — classe inesperada, nunca deveria casar
          ],
          "fill-opacity": 0.7,
          "fill-outline-color": "#24404F33",
        },
      });
    });
    return () => {
      cancelado = true;
    };
  }, [pronto]); // eslint-disable-line react-hooks/exhaustive-deps

  // Camadas de contexto (topônimos, rodovias, ferrovia — OSM, ODbL, nível A):
  // carregadas uma vez, iguais em todos os anos-âncora e em ambas as páginas que usam
  // este componente (Mapa e Narrativa). Adicionadas DEPOIS das camadas classificadas
  // (efeito seguinte na ordem de pintura): a malha viária serve de referência de
  // leitura sobre as manchas classificadas, então fica por cima delas
  // (`map.moveLayer` sem `beforeId` a move ao topo do stack assim que é criada); os
  // rótulos de topônimo são `Marker` de DOM (não há camada `symbol`: o estilo omite
  // `glyphs` de propósito), então já ficam visualmente acima de qualquer camada do
  // canvas por serem elementos HTML sobrepostos, sem precisar de ordenação de camada.
  useEffect(() => {
    if (!pronto) return;
    const map = mapRef.current;
    let cancelado = false;

    (async () => {
      const [vias, ferrovia, lugares, aerodromo] = await Promise.all([
        carregarGeojson("osm_vias", null),
        carregarGeojson("osm_ferrovia", null),
        carregarGeojson("osm_lugares", null),
        carregarGeojson("osm_aerodromo", null),
      ]);
      if (cancelado) return;

      if (!map.getSource("osm-vias")) {
        map.addSource("osm-vias", { type: "geojson", data: vias });
        map.addLayer({
          id: "layer-osm-vias",
          type: "line",
          source: "osm-vias",
          layout: {
            visibility: camadasAtivasRef.current.osm_vias ? "visible" : "none",
            "line-cap": "round",
            "line-join": "round",
          },
          paint: {
            "line-color": "#5B6B73",
            // Espessura por classe funcional: trunk (N7 — eixo Tete–Moatize) > primary
            // > secondary > tertiary, para a N7 permanecer legível mesmo com muitas
            // vias terciárias na mesma área.
            "line-width": [
              "match",
              ["get", "highway"],
              "trunk", 3.2,
              "primary", 2.4,
              "secondary", 1.7,
              "tertiary", 1.1,
              1,
            ],
          },
        });
        map.moveLayer("layer-osm-vias");
      }

      if (!map.getSource("osm-ferrovia")) {
        map.addSource("osm-ferrovia", { type: "geojson", data: ferrovia });
        map.addLayer({
          id: "layer-osm-ferrovia",
          type: "line",
          source: "osm-ferrovia",
          layout: {
            visibility: camadasAtivasRef.current.osm_ferrovia ? "visible" : "none",
          },
          paint: {
            // Tracejada e de cor distinta das rodovias — é a linha do Sena, relevante
            // ao corredor logístico do estudo (§1), não apenas contexto genérico.
            "line-color": "#24404F",
            "line-width": 1.8,
            "line-dasharray": [2, 1.6],
          },
        });
        map.moveLayer("layer-osm-ferrovia");
      }

      // Aeródromo de Tete / Chingodzi (IATA TET, ICAO FQTT). Duas geometrias no mesmo
      // arquivo: o POLÍGONO do sítio aeroportuário e a LINHA da pista 01/19. São
      // desenhados separadamente porque comunicam coisas diferentes — a área é uso do
      // solo (e compete visualmente com `urbano` e `industrial` ao redor), a pista é a
      // infraestrutura em si. Filtrar por `aeroway` no mesmo source evita um segundo
      // fetch e mantém a proveniência num arquivo só.
      if (!map.getSource("osm-aerodromo")) {
        map.addSource("osm-aerodromo", { type: "geojson", data: aerodromo });
        const visivel = camadasAtivasRef.current.osm_aerodromo ? "visible" : "none";
        map.addLayer({
          id: "layer-osm-aerodromo-area",
          type: "fill",
          source: "osm-aerodromo",
          filter: ["==", ["get", "aeroway"], "aerodrome"],
          layout: { visibility: visivel },
          paint: {
            "fill-color": CORES_CAMADA.osm_aerodromo,
            // Opacidade baixa: é contexto, não pode competir com as camadas medidas.
            "fill-opacity": 0.18,
            "fill-outline-color": CORES_CAMADA.osm_aerodromo,
          },
        });
        map.addLayer({
          id: "layer-osm-aerodromo-pista",
          type: "line",
          source: "osm-aerodromo",
          filter: ["==", ["get", "aeroway"], "runway"],
          layout: { visibility: visivel, "line-cap": "butt" },
          paint: { "line-color": CORES_CAMADA.osm_aerodromo, "line-width": 3 },
        });
        map.moveLayer("layer-osm-aerodromo-area");
        map.moveLayer("layer-osm-aerodromo-pista");
      }

      if (marcadoresRef.current.length === 0) {
        for (const feat of lugares.features || []) {
          const props = feat.properties || {};
          const [lng, lat] = feat.geometry.coordinates;
          const place = classeDeLugar(props.place);
          const el = document.createElement("div");
          el.className = `mapa-rotulo mapa-rotulo--${place}`;
          el.textContent = props.name || "";
          const marker = new Marker({ element: el, anchor: "left", offset: [4, 0] })
            .setLngLat([lng, lat])
            .addTo(map);
          marcadoresRef.current.push({ marker, place });
        }
        aplicarVisibilidadeRotulos();
      }
    })();

    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pronto]);

  // Camadas dependentes do ano: recarrega a FONTE inteira a cada troca de ano
  // (corte discreto), nunca faz tween de coordenada.
  useEffect(() => {
    if (!pronto) return;
    const map = mapRef.current;
    const camadas = ["agua", "urbano", "industrial", "reassentamento", "cultivo_irrigado", "cultivo_sequeiro"];
    let cancelado = false;

    (async () => {
      for (const camada of camadas) {
        const gj = await carregarGeojson(camada, ano);
        if (cancelado) return;
        const srcId = `src-${camada}`;
        const layerId = `layer-${camada}`;
        if (map.getSource(srcId)) {
          map.getSource(srcId).setData(gj);
        } else {
          map.addSource(srcId, { type: "geojson", data: gj });
          const isPontual = camada === "cultivo_sequeiro";
          map.addLayer({
            id: layerId,
            type: "fill",
            source: srcId,
            layout: { visibility: camadasAtivas[camada] ? "visible" : "none" },
            paint: {
              "fill-color": CORES_CAMADA[camada],
              "fill-opacity": isPontual ? 0.5 : 0.65,
              "fill-outline-color": CORES_CAMADA[camada],
            },
          });
        }
      }
    })();

    return () => {
      cancelado = true;
    };
  }, [ano, pronto]); // eslint-disable-line react-hooks/exhaustive-deps

  // Visibilidade das camadas (toggle sem recarregar dado).
  useEffect(() => {
    if (!pronto) return;
    const map = mapRef.current;
    for (const [camada, ativa] of Object.entries(camadasAtivas)) {
      if (camada === "osm_lugares") {
        aplicarVisibilidadeRotulos();
        continue;
      }
      // Uma "camada" da interface pode ser MAIS DE UMA camada do MapLibre: o aeródromo
      // são duas (área e pista). Alternar só a primeira deixaria a pista visível com a
      // área desligada — um estado que o usuário não pediu e não consegue desfazer.
      const ids = ID_LAYER_POR_CAMADA[camada]
        ? [ID_LAYER_POR_CAMADA[camada]]
        : [`layer-${camada}`];
      if (camada === "osm_aerodromo") ids.push("layer-osm-aerodromo-pista");
      for (const layerId of ids) {
        if (map.getLayer(layerId)) {
          map.setLayoutProperty(layerId, "visibility", ativa ? "visible" : "none");
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [camadasAtivas, pronto]);

  return <div ref={containerRef} className="mapa-container" role="application" aria-label="Mapa temporal Tete-Moatize" />;
}
