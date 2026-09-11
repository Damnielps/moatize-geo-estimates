// Modo "Comparar dois anos" (§6): dois mapas MapLibre com câmera espelhada, o da
// esquerda (Ano A) recortado por `clip-path` até um divisor vertical arrastável
// (mouse, toque e teclado ←/→), a partir do qual aparece o mapa da direita (Ano B).
// Mesmas camadas ativas do store nos dois lados — vetorial, sem imagem de satélite de
// fundo (decisão vinculante desta tarefa). Porte do DESENHO de
// urban-canaa/web/src/components/mapa/Comparador.tsx para JSX + MapLibre puro.
import { useCallback, useEffect, useRef, useState } from "react";
import { Map as MapLibreMap, NavigationControl, setWorkerUrl } from "maplibre-gl";
import { AOI_BBOX, ANOS_ANCORA_IMAGEM } from "../../lib/data.js";
import {
  idsDaCamada,
  camadaVisivel,
  criarEstiloVazio,
  adicionarCamadaVarzea,
  adicionarCamadaAdensamento,
  adicionarContextoOsm,
  aplicarCamadasDoAno,
  montarAtribuicao,
} from "../../lib/camadasBase.js";
import { Segmentado } from "../ui.jsx";
import { useI18n } from "../../lib/i18n.jsx";

setWorkerUrl(`${import.meta.env.BASE_URL}vendor/maplibre/maplibre-gl-worker.mjs`);

/**
 * Um lado do comparador: mapa MapLibre para `ano`, camadas do store. Mesmo protocolo de
 * carga de MapaTemporal.jsx: efeitos presos à INSTÂNCIA carregada (não a um booleano),
 * camadas por ano aplicadas juntas e só pela requisição mais recente, ordem de pintura
 * fixa (lib/camadasBase.js).
 */
function useMapaLado(containerRef, ano, camadasAtivas, interativo, atribuicao) {
  const mapRef = useRef(null);
  const [mapa, setMapa] = useState(null);
  const marcadoresRef = useRef([]);
  const camadasAtivasRef = useRef(camadasAtivas);
  const anoRef = useRef(ano);
  const requisicaoAnoRef = useRef(0);
  camadasAtivasRef.current = camadasAtivas;
  anoRef.current = ano;

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
      interactive: interativo,
    });
    if (interativo) map.addControl(new NavigationControl({ showCompass: false }), "top-right");
    map.on("load", () => {
      if (vivo) setMapa(map);
    });
    mapRef.current = map;
    return () => {
      vivo = false;
      setMapa(null);
      for (const { marker } of marcadoresRef.current) marker.remove();
      marcadoresRef.current = [];
      map.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Atribuição (ODbL do contexto OSM) no idioma corrente — só no lado que a recebe.
  useEffect(() => {
    if (!mapa || !atribuicao) return;
    return montarAtribuicao(mapa, atribuicao);
  }, [mapa, atribuicao]);

  // Camadas estáticas + contexto OSM — uma vez por instância carregada.
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
    // Adensamento 2020→2025 (MODELADO, ADR 0016): só o lado cujo ano é 2025 o desenha.
    adicionarCamadaAdensamento(
      mapa,
      () => camadaVisivel("adensamento_2020_2025", camadasAtivasRef.current, anoRef.current),
      foiCancelado
    ).catch(falha);
    adicionarContextoOsm(mapa, () => camadasAtivasRef.current, foiCancelado)
      .then((marcadores) => {
        if (marcadores) marcadoresRef.current = marcadores;
      })
      .catch(falha);
    return () => {
      cancelado = true;
    };
  }, [mapa]);

  // Camadas por ano (resposta obsoleta descartada: `aplicarCamadasDoAno`).
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

  // Visibilidade.
  useEffect(() => {
    if (!mapa) return;
    for (const [camada, ativa] of Object.entries(camadasAtivas)) {
      if (camada === "osm_lugares") {
        for (const { marker, place } of marcadoresRef.current) {
          const pequeno = place === "pequeno";
          const visivel = ativa && !(pequeno && mapa.getZoom() < 10);
          marker.getElement().style.display = visivel ? "" : "none";
        }
        continue;
      }
      const ids = idsDaCamada(camada);
      // Lado cujo ano ≠ 2025 não desenha o adensamento 2020→2025 (`camadaVisivel`).
      const visivel = ativa && camadaVisivel(camada, camadasAtivas, ano);
      for (const layerId of ids) {
        if (mapa.getLayer(layerId)) mapa.setLayoutProperty(layerId, "visibility", visivel ? "visible" : "none");
      }
    }
  }, [camadasAtivas, ano, mapa]);

  return mapRef;
}

export default function Comparador({ camadasAtivas, onSair }) {
  const { t } = useI18n();
  const [anoA, setAnoA] = useState(2010);
  const [anoB, setAnoB] = useState(2025);
  const containerRef = useRef(null);
  const contA = useRef(null);
  const contB = useRef(null);
  const [divisor, setDivisor] = useState(50);
  const sincronizandoRef = useRef(false);

  const mapaA = useMapaLado(contA, anoA, camadasAtivas, true, null);
  // A atribuição fica no mapa B (direita, embaixo): o A é recortado pelo divisor e o canto
  // direito dele some sempre que o divisor não está no fim.
  const mapaB = useMapaLado(contB, anoB, camadasAtivas, false, t("mapa_atribuicao"));

  useEffect(() => {
    const mA = mapaA.current;
    const mB = mapaB.current;
    if (!mA || !mB) return;
    const espelhar = (origem, destino) => () => {
      if (sincronizandoRef.current) return;
      sincronizandoRef.current = true;
      destino.jumpTo({ center: origem.getCenter(), zoom: origem.getZoom(), bearing: origem.getBearing(), pitch: origem.getPitch() });
      sincronizandoRef.current = false;
    };
    const deAparaB = espelhar(mA, mB);
    const deBparaA = espelhar(mB, mA);
    mA.on("move", deAparaB);
    mB.on("move", deBparaA);
    return () => {
      mA.off("move", deAparaB);
      mB.off("move", deBparaA);
    };
  }, [mapaA, mapaB]);

  const moverDivisor = useCallback((clientX) => {
    const el = containerRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const p = Math.min(100, Math.max(0, ((clientX - r.left) / r.width) * 100));
    setDivisor(p);
  }, []);

  function iniciarArraste(e) {
    e.currentTarget.setPointerCapture(e.pointerId);
    function mover(ev) {
      moverDivisor(ev.clientX);
    }
    function soltar() {
      window.removeEventListener("pointermove", mover);
      window.removeEventListener("pointerup", soltar);
    }
    window.addEventListener("pointermove", mover);
    window.addEventListener("pointerup", soltar);
  }

  function teclado(e) {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      setDivisor((d) => Math.max(0, d - 2));
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      setDivisor((d) => Math.min(100, d + 2));
    }
  }

  return (
    <div className="comparador">
      <div className="comparador__cab">
        <SeletorAno rotulo={t("comparar_ano_a")} valor={anoA} onChange={setAnoA} />
        <SeletorAno rotulo={t("comparar_ano_b")} valor={anoB} onChange={setAnoB} />
        {onSair ? (
          <button type="button" className="botao-texto" onClick={onSair}>
            {t("comparar_sair")}
          </button>
        ) : null}
      </div>
      <div className="comparador__mapas" ref={containerRef}>
        <div className="comparador__mapa comparador__mapa--b" ref={contB} />
        <div
          className="comparador__mapa comparador__mapa--a"
          style={{ clipPath: `polygon(0 0, ${divisor}% 0, ${divisor}% 100%, 0 100%)` }}
        >
          <div className="comparador__mapa-interno" ref={contA} />
        </div>
        <div className="comparador__rotulo comparador__rotulo--a">{anoA}</div>
        <div className="comparador__rotulo comparador__rotulo--b">{anoB}</div>
        <div
          className="comparador__divisor"
          style={{ left: `${divisor}%` }}
          role="separator"
          tabIndex={0}
          aria-orientation="vertical"
          aria-label={t("comparar_divisor")}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={Math.round(divisor)}
          onKeyDown={teclado}
          onPointerDown={iniciarArraste}
        >
          <span className="comparador__alca" />
        </div>
      </div>
    </div>
  );
}

function SeletorAno({ rotulo, valor, onChange }) {
  return (
    <Segmentado
      rotulo={rotulo}
      opcoes={ANOS_ANCORA_IMAGEM.map((a) => ({ valor: a, rotulo: String(a) }))}
      valor={valor}
      onChange={onChange}
    />
  );
}
