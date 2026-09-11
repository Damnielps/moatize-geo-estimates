// Objetos de contexto React do app — e NADA mais neste módulo.
//
// Motivo: `i18n.jsx` e `store.jsx` exportam, além do Provider e do hook, valores que não
// são componentes (DICIONARIO, interpolarComPartes, ANO_PADRAO, anoDeParametro). O Fast
// Refresh do Vite não os aceita como fronteira de atualização ("Could not Fast Refresh
// ... export is incompatible") e REAVALIA o módulo a cada edição. Com o `createContext`
// dentro deles, cada reavaliação criava um contexto NOVO: parte da árvore passava a ler o
// contexto novo enquanto o Provider montado ainda fornecia o antigo, e `useI18n` via
// `null` — "useI18n precisa de I18nProvider", três vezes (render duplo do StrictMode +
// nova tentativa do React), mesmo com todos os componentes dentro do Provider. Aqui o
// contexto tem identidade estável: este arquivo não muda quando o dicionário ou o store
// mudam, então não é reavaliado e o objeto de contexto é o mesmo para toda a árvore.
import { createContext } from "react";

export const I18nContext = createContext(null);
I18nContext.displayName = "I18nContext";

export const StoreContext = createContext(null);
StoreContext.displayName = "StoreContext";
