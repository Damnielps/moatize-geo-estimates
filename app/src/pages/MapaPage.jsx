import { useState } from "react";
import MapaTemporal from "../components/MapaTemporal.jsx";
import SliderTemporal from "../components/SliderTemporal.jsx";
import PainelCamadas from "../components/PainelCamadas.jsx";
import PainelEstatisticas from "../components/PainelEstatisticas.jsx";
import { useStore } from "../lib/store.jsx";
import { useI18n } from "../lib/i18n.jsx";

export default function MapaPage() {
  const { ano, setAno, anosDisponiveis, camadasAtivas, setCamadasAtivas, unidade, setUnidade } = useStore();
  const { t } = useI18n();
  const [manifest, setManifest] = useState(null);

  return (
    <div>
      <h2>{t("nav_mapa")}</h2>
      <div className="mapa-layout">
        <div className="mapa-coluna-principal">
          <SliderTemporal ano={ano} anos={anosDisponiveis} onChange={setAno} />
          <div className="mapa-slider-marcadores">
            {anosDisponiveis.map((a) => (
              <span key={a}>{a}</span>
            ))}
          </div>
          <MapaTemporal ano={ano} camadasAtivas={camadasAtivas} onManifest={setManifest} />
        </div>
        <div className="painel-lateral">
          <PainelCamadas camadasAtivas={camadasAtivas} setCamadasAtivas={setCamadasAtivas} ano={ano} manifest={manifest} />
          <PainelEstatisticas ano={ano} unidade={unidade} setUnidade={setUnidade} />
        </div>
      </div>
    </div>
  );
}
