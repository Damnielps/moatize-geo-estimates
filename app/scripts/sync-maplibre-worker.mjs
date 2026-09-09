#!/usr/bin/env node
/**
 * Copia o worker do MapLibre e o seu módulo compartilhado para `public/vendor/maplibre/`.
 *
 * ## Por que isto existe
 *
 * O MapLibre monta a URL do worker sozinho, com
 * `new URL("./maplibre-gl-worker.mjs", import.meta.url)`. No build de produção
 * `import.meta.url` é `/assets/index-<hash>.js`, logo a URL vira
 * `/assets/maplibre-gl-worker.mjs` — arquivo que o Vite nunca emite. O worker responde
 * 404 e **morre em silêncio**: nenhuma exceção, nenhum evento `error`, `npm run build`
 * passa. O sintoma é o mapa pintando só o fundo, com `isSourceLoaded()` falso em TODAS
 * as fontes e `queryRenderedFeatures()` devolvendo zero. Em dev o arquivo existe, mas o
 * Vite lhe injeta `import "/@vite/client"`, que quebra dentro de um Worker — mesmo
 * sintoma, causa diferente.
 *
 * `?url` sozinho não resolve: ele copia o worker verbatim, e o worker importa
 * `./maplibre-gl-shared.mjs` por caminho relativo — que o Vite emite com hash e sob
 * outro nome. Os DOIS arquivos têm de ficar lado a lado, com os nomes originais.
 * `public/` é servido verbatim em dev e copiado tal e qual no build, então um caminho
 * fixo lá é o único que vale nos dois modos.
 *
 * Idempotente: reescreve sempre, para não servir worker de uma versão antiga do pacote.
 */
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const APP = dirname(dirname(fileURLToPath(import.meta.url)));
const ORIGEM = join(APP, "node_modules", "maplibre-gl", "dist");
const DESTINO = join(APP, "public", "vendor", "maplibre");

// O worker importa o shared por caminho relativo: a ordem não importa, a vizinhança sim.
const ARQUIVOS = ["maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"];

mkdirSync(DESTINO, { recursive: true });
for (const nome of ARQUIVOS) {
  copyFileSync(join(ORIGEM, nome), join(DESTINO, nome));
}
console.log(`sync-maplibre-worker: ${ARQUIVOS.length} arquivos -> public/vendor/maplibre`);
