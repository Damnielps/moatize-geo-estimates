import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// SEO: a URL final (GitHub Pages) ainda não foi decidida -- não existe remote git
// configurado neste repositório. index.html usa o placeholder literal "__SITE_URL__"
// (canonical, OG/Twitter, JSON-LD); este plugin o substitui pelo valor de SITE_URL no
// build. Em dev, ou se a variável não estiver definida, cai para um domínio inválido de
// propósito (RFC 2606) para nunca publicar por engano uma URL real ou inventada.
function siteUrlPlugin() {
  // '||', não '??': no CI, uma variável de repositório (vars.SITE_URL) não configurada
  // chega como string vazia, não undefined -- '??' não cairia no padrão nesse caso.
  const siteUrl = (process.env.SITE_URL || 'https://EXEMPLO.invalid').replace(/\/$/, '')
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
