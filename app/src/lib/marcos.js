// Linha do tempo de eventos (§2, §6 do CLAUDE.md) — carrega data/app/marcos.json
// (gerado por pipeline/05_app/gerar_marcos.py a partir de config/marcos.yaml, copiado
// para app/public/data/app/marcos.json por scripts/sync-data.mjs). Nenhum ano, fonte
// ou rótulo é digitado aqui: tudo vem do JSON. Arquivo ausente ⇒ listas vazias, sem
// quebrar o SliderTemporal (§4.0 — sem o dado, o app não inventa).
import { useEffect, useState } from "react";
import { carregarJson } from "./data.js";
import { useI18n } from "./i18n.jsx";

const CAMINHO = "app/marcos.json";

function comRotulo(lista, lang) {
  return (lista ?? []).map((m) => ({
    ...m,
    rotulo: (lang === "en" ? m.rotulo_en : m.rotulo_pt) ?? m.rotulo_pt ?? m.rotulo_en ?? m.id,
  }));
}

/**
 * Hook de acesso à linha do tempo de eventos. Devolve:
 * - `fases`: períodos da periodização analítica (§2), com `ano_inicio`/`ano_fim`
 *   decimais já calculados pelo pipeline (ponto médio entre o fim de uma fase e o
 *   início da seguinte — cobertura contínua, sem lacuna nem sobreposição).
 * - `pontuais`: marcos que não são censo (concessão, licença, obras, reassentamento,
 *   operação, preço, logística, saída), cada um com `tipo`, `nivel` (A/secundario/C),
 *   `fonte`, `url`, `nota`.
 * - `censos`: marcos de `tipo === "censo"` (inclui o censo 2027 previsto).
 * - `carregando`/`erro`.
 */
export function useMarcos() {
  const { lang } = useI18n();
  const [dados, setDados] = useState(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);
    carregarJson(CAMINHO)
      .then((json) => {
        if (!cancelado) setDados(json);
      })
      .catch((e) => {
        if (!cancelado) {
          setDados(null);
          setErro(e);
        }
      })
      .finally(() => {
        if (!cancelado) setCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, []);

  const marcos = dados?.marcos ?? [];
  const fases = comRotulo(dados?.fases ?? [], lang);
  const censos = comRotulo(
    marcos.filter((m) => m.tipo === "censo"),
    lang
  );
  const pontuais = comRotulo(
    marcos.filter((m) => m.tipo !== "censo"),
    lang
  );

  return { fases, pontuais, censos, carregando, erro };
}
