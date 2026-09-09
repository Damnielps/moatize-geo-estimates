import { HashRouter, Routes, Route, NavLink } from "react-router-dom";
import { I18nProvider, useI18n } from "./lib/i18n.jsx";
import { StoreProvider } from "./lib/store.jsx";
import MapaPage from "./pages/MapaPage.jsx";
import DemografiaPage from "./pages/DemografiaPage.jsx";
import GraficosPage from "./pages/GraficosPage.jsx";
import NarrativaPage from "./pages/NarrativaPage.jsx";
import ArtigoPage from "./pages/ArtigoPage.jsx";
import MetodologiaPage from "./pages/MetodologiaPage.jsx";

function Cabecalho() {
  const { t, lang, toggleLang } = useI18n();
  return (
    <header className="ard-header">
      <h1>{t("titulo_app")}</h1>
      <nav aria-label="Navegação principal">
        <NavLink to="/" end>{t("nav_mapa")}</NavLink>
        <NavLink to="/populacao">{t("nav_populacao")}</NavLink>
        <NavLink to="/graficos">{t("nav_graficos")}</NavLink>
        <NavLink to="/narrativa">{t("nav_narrativa")}</NavLink>
        <NavLink to="/artigo">{t("nav_artigo")}</NavLink>
        <NavLink to="/metodologia">{t("nav_metodologia")}</NavLink>
        <button type="button" className="lang-toggle" onClick={toggleLang} aria-label="Trocar idioma / switch language">
          {lang === "pt" ? "EN" : "PT"}
        </button>
      </nav>
    </header>
  );
}

function Rodape() {
  return (
    <footer className="ard-footer">
      Sistema Ardósia · dados de <code>data/processed/</code> · sem backend, sem chave de API ·{" "}
      classificação própria (Landsat/Sentinel-2), WSF Evolution (DLR), GHSL (JRC), COD-AB/COD-PS (HDX).
      Nenhuma leitura causal deste app é sustentada sem o veredito da Fase 3 ao lado.
    </footer>
  );
}

export default function App() {
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
      <main id="conteudo-principal" className="ard-main" tabIndex={-1}>
        <Routes>
          <Route path="/" element={<MapaPage />} />
          <Route path="/populacao" element={<DemografiaPage />} />
          <Route path="/graficos" element={<GraficosPage />} />
          <Route path="/narrativa" element={<NarrativaPage />} />
          <Route path="/artigo" element={<ArtigoPage />} />
          <Route path="/metodologia" element={<MetodologiaPage />} />
        </Routes>
      </main>
      <Rodape />
    </>
  );
}
