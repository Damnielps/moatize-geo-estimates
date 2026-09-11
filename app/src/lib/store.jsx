import { useContext, useState, useMemo } from "react";
import { StoreContext } from "./contextos.js";
import { ANOS_ANCORA_IMAGEM } from "./data.js";

// Ano exibido quando a URL não traz `?ano=` válido.
export const ANO_PADRAO = 2025;

/**
 * `?ano=` válido (âncora de imagem) → número; ausente → null; inválido → ANO_PADRAO.
 * Nunca devolve um ano fora de ANOS_ANCORA_IMAGEM.
 */
export function anoDeParametro(bruto) {
  if (bruto == null) return null;
  const n = Number(bruto);
  return ANOS_ANCORA_IMAGEM.includes(n) ? n : ANO_PADRAO;
}

// Valor inicial lido do hash (`#/mancha?ano=2010`) ANTES do primeiro render: sem isto o
// store nasce em 2025 e o efeito store→URL de MapaPage reescreve a URL antes de ela ser
// lida — era a corrida que fazia o recarregamento de `?ano=2010` virar `?ano=2025`.
function anoInicialDaUrl() {
  if (typeof window === "undefined") return ANO_PADRAO;
  const hash = window.location.hash || "";
  const q = hash.indexOf("?");
  if (q < 0) return ANO_PADRAO;
  return anoDeParametro(new URLSearchParams(hash.slice(q + 1)).get("ano")) ?? ANO_PADRAO;
}

export function StoreProvider({ children }) {
  const [ano, setAno] = useState(anoInicialDaUrl);
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
  // Estado de reprodução do slider temporal (SliderTemporal.jsx) — vive no store, não
  // no componente, para que a Página de Mapa e o modo Narrativa possam ler/pausar a
  // mesma reprodução (§6).
  const [tocando, setTocando] = useState(false);

  const value = useMemo(
    () => ({
      ano,
      setAno,
      anosDisponiveis: ANOS_ANCORA_IMAGEM,
      unidade,
      setUnidade,
      camadasAtivas,
      setCamadasAtivas,
      tocando,
      setTocando,
    }),
    [ano, unidade, camadasAtivas, tocando]
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore() {
  const ctx = useContext(StoreContext);
  if (!ctx) throw new Error("useStore precisa de StoreProvider");
  return ctx;
}
