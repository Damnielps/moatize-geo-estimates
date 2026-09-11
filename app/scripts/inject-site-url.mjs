// Substitui o placeholder "__SITE_URL__" nos arquivos estáticos de app/public/ que o
// Vite copia verbatim para dist/ (ele só reescreve index.html via transformIndexHtml,
// ver vite.config.js). Roda depois de `vite build` no script "build" do package.json.
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { SITE_URL as SITE_URL_PUBLICACAO } from "../src/lib/publicacao.js";

const __dirname = dirname(fileURLToPath(import.meta.url));
const DIST = join(__dirname, "..", "dist");
// '||', não '??': no CI, uma variável de repositório não configurada chega como string
// vazia, não undefined. Sem a variável de ambiente, cai para a mesma constante de
// app/src/lib/publicacao.js usada por vite.config.js e por "Como citar" -- única fonte
// de verdade, nunca um domínio inventado aqui.
const SITE_URL = (process.env.SITE_URL || SITE_URL_PUBLICACAO).replace(/\/$/, "");

const ARQUIVOS = ["robots.txt", "sitemap.xml"];

for (const nome of ARQUIVOS) {
  const caminho = join(DIST, nome);
  if (!existsSync(caminho)) {
    console.warn(`[inject-site-url] ${nome} não encontrado em dist/ — pulei.`);
    continue;
  }
  const conteudo = readFileSync(caminho, "utf8");
  writeFileSync(caminho, conteudo.replaceAll("__SITE_URL__", SITE_URL));
  console.log(`[inject-site-url] ${nome}: __SITE_URL__ -> ${SITE_URL}`);
}
