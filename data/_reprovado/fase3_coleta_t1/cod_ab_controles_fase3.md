# data/provenance_parts/cod_ab_controles_fase3.md

Proveniência de COD-AB Moçambique (limites administrativos) para 5 capitais de controle.

## COD-AB Moçambique — Limites Nível 3 (Postos Administrativos)

**Status:** PENDENTE — coleta em progresso

| Atributo | Valor |
|----------|-------|
| **URL de acesso** | https://data.humdata.org/dataset/cod-ab-moz |
| **Produtora** | ITOS (Instituto de Telecomunicações de Moçambique) + MADER (Ministério da Administração Estatal) |
| **Plataforma de distribuição** | HDX (Humanitarian Data Exchange) |
| **Resolução geográfica** | Nível 0–3: país, províncias (10), distritos (~130), postos (~411) |
| **Tipo de dado** | Vetores (GeoJSON/GeoPackage); EPSG:4326 |
| **Licença** | CC-BY 4.0 |
| **Citação** | "COD-AB Moçambique. ITOS/MADER, distribuído por HDX. CC-BY 4.0." |
| **Data de verificação de acesso** | 2026-09-08 |
| **Status de download** | ⚠ Pendente; HDX oferece múltiplas opções de formato (shapefile, GeoPackage, GeoJSON). Preferir GeoJSON. |
| **Script de coleta** | Planejado em `pipeline/00_fetch/fetch_cod_ab_moz.py` |

### Especificação Técnica de Download

- **Arquivo**: Prefixo `moz_adm` (ex: `moz_adm3.geojson` para postos; `moz_adm2.geojson` para distritos)
- **Campos esperados**: `ADM0_NAME` (Moçambique), `ADM1_NAME` (província), `ADM2_NAME` (distrito), `ADM3_NAME` (posto), `P_CODE` (código único)
- **CRS**: EPSG:4326 (WGS84)
- **Validação**: Conferir que 411 postos estão presentes; normalizar nomes (acentos, maiúsculas)

### Junção com COD-PS (População)

**Chave de junção:** `ADM2_NAME` + `ADM3_NAME` normalizado (casing, acentos), **NUNCA P-CODE** (incompatível entre COD-AB e COD-PS).

**Exemplo de normalização:**
- COD-AB: "Cidade de Chimoio"
- COD-PS (INE): "Chimoio" (sem "Cidade de")
- Chave: ("Manica", "chimoio") após normalização

### Uso Metodológico (Fase 3)

- **Demarcação de unidades urbanas**: limites oficiais das 5 cidades de controle
- **Junção com população (§4.1 COD-PS)**: série 2017–presente por unidade administrativa
- **Validação de área construída**: comparar área polígono oficial vs. área classificada em imagens (§5.2)
- **Séries interrompidas**: testar parallelismo de tendência pré-2005 entre treated (Tete) e controls usando limites oficiais

