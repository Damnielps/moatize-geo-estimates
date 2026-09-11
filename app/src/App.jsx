import { useEffect } from "react";
import { HashRouter, Routes, Route, NavLink, Navigate } from "react-router-dom";
import { I18nProvider, useI18n } from "./lib/i18n.jsx";
import { StoreProvider } from "./lib/store.jsx";
import MapaPage from "./pages/MapaPage.jsx";
import DemografiaPage from "./pages/DemografiaPage.jsx";
import GraficosPage from "./pages/GraficosPage.jsx";
import InicioPage from "./pages/InicioPage.jsx";
import ArtigoPage from "./pages/ArtigoPage.jsx";
import MetodologiaPage from "./pages/MetodologiaPage.jsx";
import ProvinciaPage from "./pages/ProvinciaPage.jsx";
import ComoCitar from "./components/ComoCitar.jsx";
import { DOI, REPO_URL, VERSAO } from "./lib/publicacao.js";

function Cabecalho() {
  const { t, lang, toggleLang } = useI18n();
  return (
    <header className="ard-header">
      <h1>{t("titulo_app")}</h1>
      <nav aria-label="Navegação principal">
        <NavLink to="/" end>{t("nav_inicio")}</NavLink>
        <NavLink to="/mancha">{t("nav_mancha")}</NavLink>
        <NavLink to="/provincia">{t("nav_provincia")}</NavLink>
        <NavLink to="/populacao">{t("nav_populacao")}</NavLink>
        <NavLink to="/graficos">{t("nav_graficos")}</NavLink>
        <NavLink to="/artigo">{t("nav_artigo")}</NavLink>
        <NavLink to="/metodologia">{t("nav_metodologia")}</NavLink>
        <button type="button" className="lang-toggle" onClick={toggleLang} aria-label="Trocar idioma / switch language">
          {lang === "pt" ? "EN" : "PT"}
        </button>
      </nav>
    </header>
  );
}

// Rodapé no FIM do conteúdo rolável, não fixo (antes ocupava ~180 px permanentes e
// cortava o mapa em 1440×900). Compacto, como o painel irmão (urban-canaa `.rodape`):
// linha 1 = atribuição de fontes (quebra se precisar); linha 2 = versão · licença ·
// repositório; "Como citar" num <details> fechado. Nenhum crédito de fonte foi retirado
// (item do checklist de publicação). Fica fora de <main> para manter o landmark
// `contentinfo`.
function Rodape() {
  const { t } = useI18n();
  return (
    <footer className="ard-footer">
      <p className="ard-footer__linha">
        {t("rodape_atribuicao_prefixo")} <code>data/processed/</code> {t("rodape_atribuicao_sufixo")}
      </p>
      <p className="ard-footer__linha">
        {t("rodape_versao")} {VERSAO}
        {DOI ? (
          <>
            {" "}
            · {t("como_citar_doi")}: <a href={`https://doi.org/${DOI}`}>{DOI}</a>
          </>
        ) : null}
        {" "}· {t("rodape_licenca")}
        {" "}· {t("rodape_repositorio")}: <a href={REPO_URL} target="_blank" rel="noopener noreferrer">{REPO_URL}</a>
      </p>
      <details className="ard-footer__citar">
        <summary>{t("como_citar_titulo")}</summary>
        <ComoCitar />
      </details>
    </footer>
  );
}

export default function App() {
  // O rodapé estático de index.html (fora de #root) existe para quem abre a página sem
  // JavaScript. Com o app montado, o <Rodape> acima traz os mesmos créditos no fim da
  // área rolável; o estático, deixado visível, somava sua altura à do documento, a
  // janela passava a rolar junto com `.ard-rolagem` e o cabeçalho saía da tela.
  useEffect(() => {
    document.getElementById("rodape-estatico")?.setAttribute("hidden", "");
  }, []);
  return (
    <I18nProvider>
      <StoreProvider>
        <HashRouter>
          <div className="ard-app-shell">
            <ConteudoComSkipLink />
          </div>
        </HashRouter>
      </StoreProvider>
    </I18nProvider>
  );
}

function ConteudoComSkipLink() {
  const { t } = useI18n();
  return (
    <>
      <a href="#conteudo-principal" className="skip-link">{t("skip_link")}</a>
      <Cabecalho />
      {/* `.ard-rolagem` é a área rolável: <main> ocupa pelo menos a altura útil (o mapa
          da aba Mancha a preenche) e o rodapé vem depois, alcançado rolando. */}
      <div className="ard-rolagem">
        <main id="conteudo-principal" className="ard-main" tabIndex={-1}>
          <Routes>
            <Route path="/" element={<InicioPage />} />
            <Route path="/mancha" element={<MapaPage />} />
            <Route path="/provincia" element={<ProvinciaPage />} />
            <Route path="/populacao" element={<DemografiaPage />} />
            <Route path="/graficos" element={<GraficosPage />} />
            {/* A narrativa agora é a página inicial; o endereço antigo continua válido. */}
            <Route path="/narrativa" element={<Navigate to="/" replace />} />
            <Route path="/artigo" element={<ArtigoPage />} />
            <Route path="/metodologia" element={<MetodologiaPage />} />
          </Routes>
        </main>
        <Rodape />
      </div>
    </>
  );
}
