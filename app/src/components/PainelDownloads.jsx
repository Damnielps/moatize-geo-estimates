import { urlDownload } from "../lib/data.js";
import { useI18n } from "../lib/i18n.jsx";

const CITACAO_CLASSIFICACAO =
  "Classificação própria (Landsat C2 L2 / Sentinel-2 L2A, USGS/Copernicus, nível A). " +
  "Ver app/Metodologia (PROVENANCE.md, data/DATA_AUDIT.md) para o método completo.";

const CITACAO_LUZ =
  "Chen, Z., Yu, B. et al. (2021). \"An extended time series (2000–2018) of global NPP-VIIRS-like " +
  "nighttime light data from a cross-sensor calibration.\" Earth System Science Data, 13, 889–906. " +
  "DOI: 10.5194/essd-13-889-2021. Dataset: Chen, Z., Yu, B. et al., \"The global NPP-VIIRS-like " +
  "nighttime light data (Version 2), 1992–2025\", Harvard Dataverse, V10, DOI: 10.7910/DVN/YGIVCD (CC0 1.0). " +
  "O prefixo de arquivo \"viirs_like_li2020_\" é herança de um erro de nomeação do coletor: NÃO é o " +
  "produto de Li, X. et al. (2020, Scientific Data, nível B, não usado neste estudo).";

const CITACAO_CAUSAL =
  "Desenho causal próprio (Fase 3), sobre séries de nível A. Com 1 unidade tratada e 5 doadoras, " +
  "o piso aritmético de p por permutação é 1/6 ≈ 0,167: nenhum valor de p aqui pode ser lido como " +
  "significância convencional. Ver causal/veredito_fase3.csv — todas as quebras testadas têm " +
  "contrafactual NÃO SUSTENTADO ou não estimável.";

const CITACAO_COD =
  "Humanitarian Data Exchange, COD-AB/COD-PS Moçambique (INE/ITOS), P-codes oficiais, licença de " +
  "atribuição exigida.";

const ARQUIVOS = [
  { rotulo: "Estatísticas por ano e unidade", caminho: "csv/stats_by_year_by_unit.csv", citacao: CITACAO_CLASSIFICACAO },
  { rotulo: "Área construída por ano (AOI)", caminho: "csv/area_construida_por_ano.csv", citacao: CITACAO_CLASSIFICACAO },
  { rotulo: "Pegada industrial/reassentamento por ano", caminho: "csv/pegada_por_ano.csv", citacao: CITACAO_CLASSIFICACAO },
  { rotulo: "Cultivo por ano", caminho: "csv/cultivo_por_ano.csv", citacao: CITACAO_CLASSIFICACAO },
  { rotulo: "Cultivo em várzea por ano", caminho: "csv/cultivo_varzea_por_ano.csv", citacao: CITACAO_CLASSIFICACAO },
  { rotulo: "Acurácia da classificação por ano", caminho: "csv/acuracia_por_ano.csv", citacao: CITACAO_CLASSIFICACAO },
  { rotulo: "Série anual de luzes noturnas harmonizadas (Tete e controles)", caminho: "causal/serie_luzes_anual.csv", citacao: CITACAO_LUZ },
  { rotulo: "Veredito do desenho causal (Fase 3)", caminho: "causal/veredito_fase3.csv", citacao: CITACAO_CAUSAL },
  { rotulo: "Efeitos DiD/controle sintético e p por permutação (piso 1/6)", caminho: "causal/did_efeitos.csv", citacao: CITACAO_CAUSAL },
  { rotulo: "Testes de placebo (temporal e espacial)", caminho: "causal/placebos.csv", citacao: CITACAO_CAUSAL },
  { rotulo: "Camada urbano — 2025 (GeoJSON)", caminho: "imagery/urbano_2025.geojson", citacao: CITACAO_CLASSIFICACAO },
  { rotulo: "Camada industrial — 2025 (GeoJSON)", caminho: "imagery/industrial_2025.geojson", citacao: CITACAO_CLASSIFICACAO },
  { rotulo: "Camada reassentamento — 2025 (GeoJSON)", caminho: "imagery/reassentamento_2025.geojson", citacao: CITACAO_CLASSIFICACAO },
];

const CITACAO_GERAL =
  "Estudo \"Urbanização induzida pela mineração em Tete e Moatize (Moçambique), 1997–2025\". " +
  "Cada arquivo abaixo tem sua citação própria (fonte primária de nível A), listada ao lado do link — " +
  "cite a fonte primária, não este repositório, como origem do dado. Ver app/Metodologia para a cadeia " +
  "de proveniência completa (PROVENANCE.md, data/DATA_AUDIT.md, data/LICENSES.md).";

export default function PainelDownloads() {
  const { t } = useI18n();
  return (
    <section className="ard-card" aria-label={t("baixar_dados")}>
      <p className="ard-kicker">{t("baixar_dados")}</p>
      <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 10 }}>
        {ARQUIVOS.map((a) => (
          <li key={a.caminho}>
            <a href={urlDownload(a.caminho)} download style={{ fontSize: 13 }}>
              {a.rotulo}
            </a>
            <p style={{ fontSize: 11, color: "var(--ard-text-3)", margin: "2px 0 0" }}>{a.citacao}</p>
          </li>
        ))}
      </ul>
      <p style={{ fontSize: 11, color: "var(--ard-text-3)", marginTop: 10 }}>{CITACAO_GERAL}</p>
    </section>
  );
}
