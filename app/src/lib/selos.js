// Helpers de selo (observado/interpolado/modelado) e nível de fonte (A/B/C) — §10:
// "toda série temporal com selo observado/interpolado/modelado". Extraído de
// DemografiaPage.jsx para reúso em outras páginas/componentes (ex.: Kpi em ui.jsx).
// Arquivo .js (não .jsx): usa React.createElement em vez de sintaxe JSX.
import { createElement } from "react";

// Ordem de "pior selo" — §10: observado é a leitura mais firme, modelado a menos.
// Um gráfico que combina pontas de selos diferentes (razão, índice multi-unidade)
// herda o PIOR dos dois, nunca o melhor nem uma etiqueta inventada como "derivado".
export const ORDEM_SELO = { observado: 0, interpolado: 1, modelado: 2 };

export function piorSelo(a, b) {
  if (!a) return b ?? null;
  if (!b) return a ?? null;
  return (ORDEM_SELO[a] ?? 99) >= (ORDEM_SELO[b] ?? 99) ? a : b;
}

// Selo de um cartão inteiro = união (ordenada, sem repetição) dos selos das linhas do
// CSV efetivamente plotadas nele — nunca escrito à mão no JSX.
export function juntarSelos(selos) {
  const unicos = [...new Set(selos.filter(Boolean))];
  unicos.sort((a, b) => (ORDEM_SELO[a] ?? 99) - (ORDEM_SELO[b] ?? 99));
  return unicos.join(" / ") || null;
}

export const ORDEM_NIVEL = { A: 0, B: 1, C: 2 };

export function piorNivel(a, b) {
  if (!a) return b ?? null;
  if (!b) return a ?? null;
  return (ORDEM_NIVEL[a] ?? 99) >= (ORDEM_NIVEL[b] ?? 99) ? a : b;
}

// Marcador vazado para pontos de nível de fonte B ou C (aviso obrigatório: nível no
// tooltip, marcador diferente na tela). `payload` traz o ponto inteiro construído por
// quem chama, incluindo `nivel_<unidade>` para esta série específica.
export function pontoPorNivel(chaveNivel, cor) {
  return function DotPorNivel(props) {
    const { cx, cy, payload } = props;
    const nivel = payload?.[chaveNivel];
    if (cx == null || cy == null || !payload || payload[chaveNivel.replace("nivel_", "")] == null) return null;
    const vazado = nivel === "B" || nivel === "C" || nivel === "ausente";
    return createElement("circle", {
      cx,
      cy,
      r: 4,
      fill: vazado ? "#fff" : cor,
      stroke: cor,
      strokeWidth: 2,
    });
  };
}
