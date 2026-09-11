import { useEffect, useRef, useState } from "react";
import { Map as MapLibreMap, NavigationControl, setWorkerUrl } from "maplibre-gl";
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
import { carregarJson, AOI_BBOX } from "../lib/data.js";
import {
  idsDaCamada,
  camadaVisivel,
  criarEstiloVazio,
  adicionarCamadaVarzea,
  adicionarCamadaAdensamento,
  adicionarContextoOsm,
  aplicarCamadasDoAno,
  montarAtribuicao,
} from "../lib/camadasBase.js";
import { useI18n } from "../lib/i18n.jsx";

setWorkerUrl(`${import.meta.env.BASE_URL}vendor/maplibre/maplibre-gl-worker.mjs`);

// Cores por camada, estilo vazio e ordem de pintura: lib/camadasBase.js (reúso com
// Comparador.jsx). Este módulo exporta SÓ o componente: um export não-componente
// (antes, `CORES_CAMADA`) impede o Fast Refresh de tratá-lo como fronteira e força a
// reavaliação em cadeia de quem o importa.

/**
 * Mapa MapLibre sem dependência de tile de terceiros (sem chave de API, sem serviço
 * externo): só as camadas GeoJSON de data/processed/app/imagery/. Troca de ano é corte
 * discreto de fonte de dado — NUNCA interpolação de geometria (DECISOES.md item 7,
 * ADR 0013: churn de 31-54% entre anos consecutivos tornaria uma transição suave uma
 * mentira animada de "movimento" que não existe no dado).
 */

export default function MapaTemporal({ ano, camadasAtivas, onManifest }) {
  const { t } = useI18n();
  const containerRef = useRef(null);
  const marcadoresRef = useRef([]); // { marker, place } — topônimos (DOM, sem symbol/glyphs)
  const camadasAtivasRef = useRef(camadasAtivas);
  const anoRef = useRef(ano);
  // A INSTÂNCIA de mapa cujo evento `load` já disparou — não um booleano `pronto`.
  // Com booleano, uma instância nova criada sem desmontar o componente (Fast Refresh
  // preserva o estado e re-executa os efeitos) herdava `pronto = true` da anterior e os
  // efeitos de dados rodavam sobre um estilo ainda não carregado (`addSource` lança "Style is not done loading" dentro de
  // um async: exceção não tratada, nenhuma camada vetorial, só os topônimos de DOM).
  // Cada efeito abaixo depende desta instância e só a ela aplica dados.
  const [mapa, setMapa] = useState(null);
  // Contador de requisições das camadas por ano: só a mais recente pode escrever no mapa.
  const requisicaoAnoRef = useRef(0);

  camadasAtivasRef.current = camadasAtivas;
  anoRef.current = ano;

  // Aplica visibilidade dos rótulos de topônimo combinando dois critérios independentes:
  // o toggle "osm_lugares" do painel de camadas e o zoom atual (classes pequenas —
  // suburb/hamlet/neighbourhood — ficam ilegíveis e sobrepostas em zoom baixo).
  function aplicarVisibilidadeRotulos(map) {
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
    let vivo = true;
    const map = new MapLibreMap({
      container: containerRef.current,
      style: criarEstiloVazio(),
      bounds: [
        [AOI_BBOX[0], AOI_BBOX[1]],
        [AOI_BBOX[2], AOI_BBOX[3]],
      ],
      fitBoundsOptions: { padding: 20 },
      attributionControl: false,
    });
    map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    map.on("load", () => {
      if (vivo) setMapa(map);
    });
    map.on("zoom", () => aplicarVisibilidadeRotulos(map));
    if (import.meta.env.DEV) window.__teteMoatizeMap = map; // hook de verificação em dev
    carregarJson("imagery/manifest.json")
      .then((m) => {
        if (vivo) onManifest?.(m);
      })
      .catch((e) => console.error(e));
    return () => {
      vivo = false;
      setMapa(null);
      for (const { marker } of marcadoresRef.current) marker.remove();
      marcadoresRef.current = [];
      map.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Atribuição no idioma corrente (PT/EN); refeita na troca de idioma.
  useEffect(() => {
    if (!mapa) return;
    return montarAtribuicao(mapa, t("mapa_atribuicao"));
  }, [mapa, t]);

  // Camadas estáticas, uma vez por instância de mapa carregada: várzea, adensamento
  // 2020→2025 e contexto OSM. A ordem de pintura não depende de qual chega primeiro
  // (ORDEM_CAMADAS em lib/camadasBase.js): contexto OSM por cima das manchas medidas.
  //
  // `adensamento_2020_2025` (ADR 0016) é uma síntese única do intervalo 2020→2025 (sem
  // sufixo de ano), categórica por `classe`, ligada por padrão (store.jsx), mas desenhada
  // SÓ quando o ano exibido é 2025 (`camadaVisivel`). Os topônimos são `Marker` de DOM
  // (o estilo omite `glyphs` de propósito). Visibilidade lida dos refs NA HORA da adição:
  // o GeoJSON chega depois, e o ano pode ter mudado (play) enquanto carregava.
  useEffect(() => {
    if (!mapa) return;
    let cancelado = false;
    const foiCancelado = () => cancelado;
    const falha = (e) => {
      if (!cancelado) console.error(e);
    };
    adicionarCamadaVarzea(
      mapa,
      () => camadaVisivel("varzea", camadasAtivasRef.current, anoRef.current),
      foiCancelado
    ).catch(falha);
    adicionarCamadaAdensamento(
      mapa,
      () => camadaVisivel("adensamento_2020_2025", camadasAtivasRef.current, anoRef.current),
      foiCancelado
    ).catch(falha);
    adicionarContextoOsm(mapa, () => camadasAtivasRef.current, foiCancelado)
      .then((marcadores) => {
        if (!marcadores) return;
        marcadoresRef.current = marcadores;
        aplicarVisibilidadeRotulos(mapa);
      })
      .catch(falha);
    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mapa]);

  // Camadas dependentes do ano: recarrega a FONTE inteira a cada troca de ano
  // (corte discreto), nunca faz tween de coordenada. As seis chegam em paralelo e são
  // aplicadas juntas, e só se esta for a requisição mais recente — a resposta atrasada
  // de um ano anterior é descartada (lib/camadasBase.js, `aplicarCamadasDoAno`).
  useEffect(() => {
    if (!mapa) return;
    const minha = ++requisicaoAnoRef.current;
    let cancelado = false;
    aplicarCamadasDoAno(
      mapa,
      ano,
      (camada) => camadaVisivel(camada, camadasAtivasRef.current, anoRef.current),
      () => !cancelado && minha === requisicaoAnoRef.current
    ).catch((e) => {
      if (!cancelado) console.error(e);
    });
    return () => {
      cancelado = true;
    };
  }, [ano, mapa]);

  // Visibilidade das camadas (toggle sem recarregar dado).
  useEffect(() => {
    if (!mapa) return;
    for (const [camada, ativa] of Object.entries(camadasAtivas)) {
      if (camada === "osm_lugares") {
        aplicarVisibilidadeRotulos(mapa);
        continue;
      }
      // Uma "camada" da interface pode ser MAIS DE UMA camada do MapLibre (aeródromo:
      // área e pista; classes com contorno, ADR 0018): `idsDaCamada` devolve todas.
      const ids = idsDaCamada(camada);
      // `camadaVisivel`: camada restrita a um ano (adensamento 2020→2025) não é desenhada
      // fora dele, mesmo ligada no painel — por isso este efeito depende também de `ano`.
      const visivel = ativa && camadaVisivel(camada, camadasAtivas, ano);
      for (const layerId of ids) {
        if (mapa.getLayer(layerId)) {
          mapa.setLayoutProperty(layerId, "visibility", visivel ? "visible" : "none");
        }
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [camadasAtivas, ano, mapa]);

  return <div ref={containerRef} className="mapa-container" role="application" aria-label={t("mapa_temporal_aria")} />;
}
