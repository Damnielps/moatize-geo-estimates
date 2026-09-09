import { createContext, useContext, useState, useMemo } from "react";
import { ANOS_ANCORA_IMAGEM } from "./data.js";

const StoreContext = createContext(null);

export function StoreProvider({ children }) {
  const [ano, setAno] = useState(2025);
  const [unidade, setUnidade] = useState("Cidade de Tete");
  // Estado inicial das camadas do mapa (decisão do usuário, 2026-09-09): o app abre com
  // TODAS ligadas, exceto `cultivo_sequeiro`.
  //
  // A exceção não é estética. `cultivo_sequeiro` é a única camada rotulada no painel como
  // "vegetação sazonal (NÃO confirmada como cultivo)": a fenologia de sequeiro não se
  // separa de vegetação sazonal não cultivada com a validação disponível, e ligá-la por
  // padrão apresentaria como cultivo aquilo que o estudo declara não ter confirmado.
  //
  // `adensamento_2020_2025` entra ligada, e é **modelada** (síntese de três sinais por
  // concordância, ADR 0016, publicável só como padrão espacial). O selo está no rótulo do
  // painel, na legenda e no aviso da camada — ligá-la por padrão aumenta a exposição
  // dessa ressalva, não a dispensa.
  const [camadasAtivas, setCamadasAtivas] = useState({
    urbano: true,
    industrial: true,
    reassentamento: true,
    cultivo_irrigado: true,
    cultivo_sequeiro: false,
    agua: true,
    varzea: true,
    osm_vias: true,
    osm_ferrovia: true,
    osm_lugares: true,
    osm_aerodromo: true,
    adensamento_2020_2025: true,
  });
  const [referencia, setReferencia] = useState("nenhuma");

  const value = useMemo(
    () => ({
      ano,
      setAno,
      anosDisponiveis: ANOS_ANCORA_IMAGEM,
      unidade,
      setUnidade,
      camadasAtivas,
      setCamadasAtivas,
      referencia,
      setReferencia,
    }),
    [ano, unidade, camadasAtivas, referencia]
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore precisa de StoreProvider");
  return ctx;
}
