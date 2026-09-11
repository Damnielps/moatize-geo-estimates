import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import MapaTemporal from "../components/MapaTemporal.jsx";
import SliderTemporal from "../components/SliderTemporal.jsx";
import ChurnBadge from "../components/mapa/ChurnBadge.jsx";
import Comparador from "../components/mapa/Comparador.jsx";
import PainelCamadas from "../components/PainelCamadas.jsx";
import PainelEstatisticas from "../components/PainelEstatisticas.jsx";
import { Segmentado } from "../components/ui.jsx";
import { useStore, anoDeParametro } from "../lib/store.jsx";
import { useI18n } from "../lib/i18n.jsx";

export default function MapaPage() {
  const { ano, setAno, anosDisponiveis, camadasAtivas, setCamadasAtivas, unidade, setUnidade } = useStore();
  const { t } = useI18n();
  const [manifest, setManifest] = useState(null);
  const [modo, setModo] = useState("ano"); // "ano" | "comparar"
  const [searchParams, setSearchParams] = useSearchParams();

  // `?ano=` ↔ store. A URL vence: o store já nasce com o ano do hash (store.jsx,
  // `anoInicialDaUrl`), e o efeito URL→store abaixo cobre a navegação de outra rota para
  // `#/mancha?ano=2015` e a edição manual do hash. O efeito store→URL só escreve depois
  // de a URL ter sido aplicada: enquanto há um ano pendente vindo da URL e o store ainda
  // não o refletiu, ele se abstém (senão reescreveria a URL com o ano antigo, que é a
  // corrida original). Âncora inválida (fora de ANOS_ANCORA_IMAGEM) cai em 2025.
  const anoUrlBruto = searchParams.get("ano");
  const pendenteDaUrl = useRef(null);

  useEffect(() => {
    const alvo = anoDeParametro(anoUrlBruto);
    if (alvo == null) return; // sem `?ano=`: o store prevalece e é escrito abaixo
    if (alvo !== ano) {
      pendenteDaUrl.current = alvo;
      setAno(alvo);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [anoUrlBruto]);

  useEffect(() => {
    if (pendenteDaUrl.current != null) {
      if (ano !== pendenteDaUrl.current) return; // URL ainda não aplicada ao store
      pendenteDaUrl.current = null;
    }
    if (String(ano) !== anoUrlBruto) {
      const proximos = new URLSearchParams(searchParams);
      proximos.set("ano", String(ano));
      setSearchParams(proximos, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ano, anoUrlBruto]);

  const indiceAtual = anosDisponiveis.indexOf(ano);
  const anoAnterior = indiceAtual > 0 ? anosDisponiveis[indiceAtual - 1] : null;

  return (
    <div className="mapa-pagina">
      <h2>{t("mapa_pagina_titulo")}</h2>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8, flexWrap: "wrap" }}>
        <Segmentado
          rotulo={t("mapa_modo_rotulo")}
          opcoes={[
            { valor: "ano", rotulo: t("mapa_modo_ano") },
            { valor: "comparar", rotulo: t("mapa_modo_comparar") },
          ]}
          valor={modo}
          onChange={setModo}
        />
        {modo === "ano" ? <ChurnBadge ano={ano} anoAnterior={anoAnterior} manifest={manifest} /> : null}
      </div>

      {modo === "comparar" ? (
        <Comparador camadasAtivas={camadasAtivas} />
      ) : (
        <div className="mapa-layout">
          <div className="mapa-coluna-principal">
            <SliderTemporal />
            <MapaTemporal ano={ano} camadasAtivas={camadasAtivas} onManifest={setManifest} />
          </div>
          <div className="painel-lateral">
            <PainelCamadas camadasAtivas={camadasAtivas} setCamadasAtivas={setCamadasAtivas} ano={ano} manifest={manifest} />
            <PainelEstatisticas ano={ano} unidade={unidade} setUnidade={setUnidade} />
          </div>
        </div>
      )}
    </div>
  );
}
