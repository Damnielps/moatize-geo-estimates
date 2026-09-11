import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { SITE_URL as SITE_URL_PUBLICACAO } from './src/lib/publicacao.js'

// SEO: index.html usa o placeholder literal "__SITE_URL__" (canonical, OG/Twitter,
// JSON-LD); este plugin o substitui pelo valor de SITE_URL no build. A variável de
// ambiente SITE_URL (definida no CI a partir de vars.SITE_URL) tem prioridade; sem ela,
// cai para a constante de app/src/lib/publicacao.js (mesma usada em "Como citar"),
// única fonte de verdade -- nunca um domínio inventado aqui.
function siteUrlPlugin() {
  // '||', não '??': no CI, uma variável de repositório (vars.SITE_URL) não configurada
  // chega como string vazia, não undefined -- '??' não cairia no padrão nesse caso.
  const siteUrl = (process.env.SITE_URL || SITE_URL_PUBLICACAO).replace(/\/$/, '')
  return {
    name: 'substituir-site-url',
    transformIndexHtml(html) {
      return html.replaceAll('__SITE_URL__', siteUrl)
    },
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), siteUrlPlugin()],
  // GitHub Pages de projeto serve em https://<usuário>.github.io/<repo>/ -- BASE_PATH
  // precisa ser definido no workflow de publicação (ou aqui) assim que o nome do
  // repositório for decidido. Raiz ("/") continua correta para dev e para páginas de
  // usuário/organização (<usuário>.github.io) ou domínio próprio.
  base: process.env.BASE_PATH || '/',
  build: {
    sourcemap: false,
  },
})
