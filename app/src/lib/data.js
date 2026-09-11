import Papa from "papaparse";

// Utilitários de acesso a data/processed/ (copiado para public/data/ por
// scripts/sync-data.mjs). Nada aqui inventa número: tudo vem de fetch de artefato.

const BASE = `${import.meta.env.BASE_URL}data`;

const cacheCsv = new Map();
const cacheJson = new Map();

export async function carregarCsv(caminho) {
  if (cacheCsv.has(caminho)) return cacheCsv.get(caminho);
  const resp = await fetch(`${BASE}/${caminho}`);
  if (!resp.ok) throw new Error(`falha ao carregar ${caminho}: ${resp.status}`);
  const texto = await resp.text();
  const { data } = Papa.parse(texto, { header: true, dynamicTyping: true, skipEmptyLines: true });
  cacheCsv.set(caminho, data);
  return data;
}

// Cache da PROMESSA, não do resultado: duas chamadas simultâneas ao mesmo caminho (dois
// efeitos do StrictMode, os dois lados do Comparador, ou o mesmo ano pedido de novo
// enquanto a primeira resposta ainda está a caminho) compartilham UMA requisição, em vez
// de disparar duas e aplicar a que chegar por último. Falha sai do cache (nova tentativa
// possível); não é engolida.
export function carregarJson(caminho) {
  if (cacheJson.has(caminho)) return cacheJson.get(caminho);
  const promessa = fetch(`${BASE}/${caminho}`)
    .then((resp) => {
      if (!resp.ok) throw new Error(`falha ao carregar ${caminho}: ${resp.status}`);
      return resp.json();
    })
    .catch((e) => {
      cacheJson.delete(caminho);
      throw e;
    });
  cacheJson.set(caminho, promessa);
  return promessa;
}

export async function carregarGeojson(camada, ano) {
  const nome = ano != null ? `${camada}_${ano}.geojson` : `${camada}.geojson`;
  return carregarJson(`imagery/${nome}`);
}

export function urlDownload(caminho) {
  return `${BASE}/${caminho}`;
}

export const ANOS_ANCORA_IMAGEM = [2000, 2005, 2010, 2015, 2020, 2025];
export const ANOS_ANCORA_CENSO = [1997, 2007, 2017];

// Bbox da AOI (config/study.yaml — não recalculado aqui, apenas citado da fonte de
// configuração do estudo).
export const AOI_BBOX = [33.5, -16.35, 34.1, -16.0];
