// Copia o subconjunto necessário de data/processed/ para app/public/data/.
// Não gera número nenhum: cópia byte a byte dos artefatos publicados pela Fase 3/3b.
// Execução: npm run sync-data (roda automaticamente antes de dev/build).
import { existsSync, mkdirSync, readdirSync, copyFileSync, statSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..", "..");
const SRC = join(ROOT, "data", "processed");
const DEST = join(__dirname, "..", "public", "data");

function ensureDir(p) {
  if (!existsSync(p)) mkdirSync(p, { recursive: true });
}

function copyDir(srcDir, destDir, filter = () => true) {
  ensureDir(destDir);
  for (const name of readdirSync(srcDir)) {
    const s = join(srcDir, name);
    const st = statSync(s);
    if (st.isFile() && filter(name)) {
      copyFileSync(s, join(destDir, name));
    }
  }
}

// 1) Camadas do mapa (GeoJSON + manifesto), já preparadas pela primeira tarefa da Fase 4.
copyDir(
  join(SRC, "app", "imagery"),
  join(DEST, "imagery"),
  (name) => name.endsWith(".geojson") || name === "manifest.json"
);

// 2) Tabelas para o painel de estatísticas e para os gráficos.
const CSV_RAIZ = [
  "stats_by_year_by_unit.csv",
  "acuracia_por_ano.csv",
  "acuracia_cultivo_por_ano.csv",
  "area_construida_por_ano.csv",
  "pegada_por_ano.csv",
  "cultivo_por_ano.csv",
  "cultivo_varzea_por_ano.csv",
  "matriz_confusao_por_ano.csv",
  "matriz_confusao_cultivo.csv",
  "concordancia_wsf.csv",
  "concordancia_ghsl.csv",
  "concordancia_externa_cultivo.csv",
  "demografia_contexto_nao_nucleo.csv",
  "populacao_dasimetrica_sensibilidade.csv",
  "pegada_sensibilidade.csv",
  "cobertura_estacao_chuvosa.csv",
  "demografia_serie_1997_2025.csv",
  "populacao_vila_moatize_sensibilidade.csv",
];
ensureDir(join(DEST, "csv"));
for (const f of CSV_RAIZ) {
  const s = join(SRC, f);
  if (existsSync(s)) copyFileSync(s, join(DEST, "csv", f));
}

// 3) Família causal — quebras, veredito, decomposição, cenários, séries de controle.
copyDir(join(SRC, "causal"), join(DEST, "causal"), (name) => name.endsWith(".csv"));

// 4) Manuscrito bruto, para o link de download da aba Artigo (o conteúdo RENDERIZADO
// vem de app/src/content/artigo.json, gerado por pipeline/05_app/gerar_artigo.py — este
// .md é só o arquivo original oferecido para baixar, igual ao padrão das demais tabelas).
const PAPER_SRC = join(ROOT, "paper", "artigo.md");
if (existsSync(PAPER_SRC)) {
  ensureDir(join(DEST, "paper"));
  copyFileSync(PAPER_SRC, join(DEST, "paper", "artigo.md"));
}

console.log("sync-data: copiado data/processed -> app/public/data");
