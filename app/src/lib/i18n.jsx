import { useContext, useState, useCallback } from "react";
import { I18nContext } from "./contextos.js";

// Bilinguismo PT (padrão) / EN — CLAUDE.md §6.7. Dicionário estático, sem serviço de
// tradução externo (nenhuma chave de API).
export const DICIONARIO = {
  pt: {
    titulo_app: "Tete–Moatize · urbanização e mineração 1997–2025",
    nav_populacao: "População",
    nav_graficos: "Gráficos",
    nav_artigo: "Artigo",
    nav_metodologia: "Metodologia",
    ano: "Ano",
    unidade: "Unidade",
    camadas: "Camadas",
    camada_urbano: "Urbano (construído)",
    camada_industrial: "Pegada industrial/minerária",
    camada_reassentamento: "Pegada de reassentamento",
    camada_cultivo_irrigado: "Cultivo irrigado / vazante",
    camada_cultivo_sequeiro: "Vegetação sazonal (não confirmada como cultivo)",
    camada_agua: "Água",
    camada_varzea: "Várzea (estática)",
    camada_osm_vias: "Rodovias (N7 e demais, OSM)",
    camada_osm_ferrovia: "Ferrovia (linha do Sena, OSM)",
    camada_osm_lugares: "Topônimos (OSM)",
    camada_osm_aerodromo: "Aeródromo de Tete — TET/FQTT (OSM)",
    camada_adensamento_2020_2025: "Adensamento 2020→2025 (modelado, concordância de 3 sinais)",
    camada_adensamento_2020_2025_indisponivel: "disponível só em 2025 (contraste 2020→2025, modelado)",
    aviso_adensamento_selo:
      "Camada MODELADA (ADR 0016): síntese de concordância entre classificação própria, tendência de luz noturna (proxy de atividade, NÃO de população) e resíduo de edificações (Open Buildings, janela real 2020→~2023, não 2020→2025). A classe “adensando” não pode ser somada a “expansão nova” — são respostas distintas.",
    aviso_adensamento_sensibilidade_prefixo: "Sensibilidade a ±1 decil dos cortes: razão",
    aviso_adensamento_riscos:
      "A área de “adensando” NÃO é publicável como número exato — só como padrão espacial e ordem de grandeza. A camada não detecta esvaziamento/desadensamento (o sinal só pode subir, por construção).",
    aviso_adensamento_sem_manifesto: "(ressalvas completas indisponíveis — manifest.json não carregado)",
    aviso_urbano_comissao:
      "Atenção: entre 37% e 71% do que este mapa chama de “urbano” não é construído — é a comissão medida ano a ano (37,5% em 2025, 71,4% em 2010), ver ADR 0009 e a reexecução do ADR 0014. A camada nunca pode diminuir entre anos por construção (catraca R2, ADR 0013).",
    aviso_sequeiro:
      "Vegetação de fenologia sazonal acentuada, NÃO confirmada como cultivo (acurácia do usuário medida = 0,000; ADR 0012).",
    nenhuma: "Nenhuma",
    churn_titulo: "Instabilidade entre este ano e o anterior",

    // --- Mapa e pegadas (Fase 4b, B2): slider temporal, badge de churn, comparador ---
    nav_mancha: "Mancha e pegadas",
    nav_provincia: "Província e cidades",
    mapa_pagina_titulo: "Mancha e pegadas",
    mapa_modo_rotulo: "Modo de exibição",
    mapa_modo_ano: "Mapa do ano",
    mapa_modo_comparar: "Comparar dois anos",
    slider_ano_anterior: "Ano-âncora anterior",
    slider_proximo_ano: "Próximo ano-âncora",
    slider_reproduzir: "Reproduzir",
    slider_pausar: "Pausar",
    slider_movimento_reduzido: "Reprodução automática desativada — o sistema pede menos movimento (prefers-reduced-motion). Use ‹ e › para avançar manualmente.",
    slider_aria_label: "Ano-âncora exibido no mapa",
    slider_fora_do_intervalo: "fora da escala exibida, ver seta",
    slider_nivel_secundario: "secundário",
    slider_nivel_c: "nível C — proibido para número publicado (§4.0)",
    marco_tipo_censo: "censo",
    marco_tipo_concessao: "concessão",
    marco_tipo_licenca: "licença",
    marco_tipo_obras: "obras",
    marco_tipo_reassentamento: "reassentamento",
    marco_tipo_operacao: "operação",
    marco_tipo_preco: "preço do carvão",
    marco_tipo_logistica: "logística",
    marco_tipo_saida: "saída/venda",
    comparar_ano_a: "Ano A (esquerda)",
    comparar_ano_b: "Ano B (direita)",
    comparar_sair: "Sair da comparação",
    comparar_divisor: "Divisor da comparação",
    churn_primeiro_ano_ancora: "2000 — primeiro ano-âncora, sem par anterior",
    churn_sem_dado: "Sem churn registrado no manifesto para este par de anos",
    churn_titulo_curto: "Instabilidade de classificação entre este ano-âncora e o anterior (classe construído)",
    churn_rotulo_curto: "Churn",
    churn_jaccard_rotulo: "Jaccard",
    churn_experimental_nota:
      "EXPERIMENTAL (ADR 0011/0013) — rótulo bruto do classificador, antes de R1/R2 e das pegadas; não substitui nenhum artefato publicado. A troca de ano no mapa é um corte discreto entre classificações independentes, nunca uma trajetória contínua.",
    rodape_atribuicao_prefixo: "Sistema Ardósia · dados de",
    rodape_atribuicao_sufixo:
      "· sem backend, sem chave de API · classificação própria (Landsat/Sentinel-2), WSF Evolution (DLR), GHSL (JRC), COD-AB/COD-PS (HDX). Nenhuma leitura causal deste app é sustentada sem o veredito da Fase 3 ao lado.",
    baixar_dados: "Baixar dados (CSV/GeoJSON) com citação",
    // --- Downloads de contexto econômico e marcos (Fase 4b, B5) ---
    download_preco_carvao_rotulo: "Preço do carvão — série anual (mercado mundial)",
    download_preco_carvao_citacao:
      "World Bank. Commodity Markets Observatory — CMO Historical Data Annual: Coal, Australian and Coal, South African (USD/mt, nominal). Licença CC BY 4.0 (ver LICENSE-DADOS.md).",
    download_contas_regionais_rotulo: "Contas regionais de Tete (PIB, inflação)",
    download_contas_regionais_marca: "nível C — contexto, não núcleo",
    download_contas_regionais_citacao:
      "INE Moçambique, Folheto Provincial Tete 2021, quadro \"PIB e Inflação\" (lido via snapshot Wayback Machine; licença não localizada em ine.gov.mz — nível C, §4.0 de CLAUDE.md). Contexto: não sustenta nenhum número do núcleo publicado deste estudo.",
    download_producao_moatize_rotulo: "Produção de carvão em Moatize (Vale) — série anual",
    download_producao_moatize_marca: "sem valores publicados ainda",
    download_producao_moatize_citacao:
      "Vale S.A., Form 20-F (SEC EDGAR, CIK 0000917851), 2008–2022 — fonte de nível A, ainda não acessada (pipeline/00_fetch/fetch_vale_20f.py aguarda configuração de SEC_USER_AGENT). Todas as linhas deste arquivo estão marcadas \"não disponível\": nenhum valor foi inventado (§4.0, §0).",
    download_marcos_rotulo: "Marcos da linha do tempo do ciclo do carvão",
    download_marcos_citacao:
      "Vale S.A., Rio Tinto plc, Human Rights Watch, SEC EDGAR, INE — documentos institucionais e regulatórios diversos. Referência bibliográfica de cada marco em data/licenses_parts/marcos.md; documentos-fonte não redistribuídos (ver LICENSE-DADOS.md).",
    fonte: "Fonte",
    metodo: "Método",
    selo: "Selo",
    ano_dado: "Ano do dado",
    nivel: "Nível de confiança",
    fechar: "Fechar",
    veredito_causal_titulo: "Veredito do desenho causal (Fase 3)",
    veredito_aviso:
      "As quatro quebras testadas (2005, 2011, 2016, 2022) têm contrafactual NÃO SUSTENTADO ou não estimável. Nenhuma leitura causal é sustentada por este estudo.",
    decomposicao_aviso:
      "A queda de 2022 NÃO pode ser atribuída à mina (ADR 0015, decisão 4). A decomposição não é partição: publica-se piso e teto, nunca um único valor.",
    aviso_ic_acuracia:
      "A acurácia do usuário vem com IC95 de ±0,20 e a classe ocupa 0,5–1,9 % da AOI. Nenhum dos 15 pares de anos-âncora tem IC95 que deixe de se sobrepor: a variação entre anos (0,286 em 2010 a 0,625 em 2025) NÃO é distinguível de ruído amostral. Leia como uma faixa única para toda a série, nunca como melhora ou piora ao longo do tempo (§10, ADR 0009).",
    piso_p_aviso:
      "Piso aritmético da inferência: com 1 unidade tratada e 5 doadoras, a inferência por permutação tem p mínimo possível = 1/6 ≈ 0,167 — nenhum resultado deste estudo pode atingir significância convencional (p < 0,05), não por fraqueza do efeito, mas por aritmética do pool de comparação. Um p perto de 0,167 é o piso do teste, não um resultado nulo comum: leia sempre junto com o piso, nunca isolado.",
    p_permutacao_titulo:
      "p por permutação (contra o piso aritmético de 1/6 ≈ 0,167; ver aviso acima)",
    anel_periurbano_ausente:
      "Anéis periurbanos por ano-âncora e modo de transições cultivo→construído ainda não existem em data/processed/ (§4.0: sem o dado, o app não o inventa). O logit espacial de conversão está registrado como NÃO DETERMINÁVEL nesta rodada (causal/logit_conversao_status.csv): o churn de 31–54% entre anos-âncora consecutivos (ADR 0013) torna 'este pixel mudou' um desfecho não identificável sem classe de origem estável. As camadas de cultivo abaixo mostram o estado de cada ano-âncora isoladamente, nunca uma transição inferida.",
    skip_link: "Pular para o conteúdo",
    metod_ambiente_titulo: "Ambiente e bibliotecas (§6-A.2)",
    metod_adr_titulo: "Decisões metodológicas — ADR (§6-A.5)",
    metod_provenance_titulo: "Proveniência (PROVENANCE.md)",
    metod_audit_titulo: "Auditoria de dados (data/DATA_AUDIT.md)",
    kpi_demografia: "Demografia / forma urbana",
    kpi_area_construida: "Área construída (AOI)",
    kpi_pegada: "Pegada industrial/reassentamento",
    kpi_agricultura: "Agricultura urbana e periurbana",
    kpi_acuracia: "Acurácia da classe \"construído\" (ADR 0009)",
    kpi_sem_linhas: "Sem linhas em stats_by_year_by_unit.csv para esta unidade/ano.",
    veredicto_secao_titulo: "O que os dados não sustentam",

    // --- Aba População (demografia_serie_1997_2025.csv) ---
    pop_titulo: "População — séries por unidade, 1997–2025",
    pop_aviso_titulo: "Como ler estas séries",
    pop_aviso_niveis:
      "Cada ponto tem nível de fonte A, B ou C (§4.0); o nível está no tooltip de cada valor. Pontos de nível B/C aparecem com marcador vazado nos gráficos.",
    pop_aviso_2025:
      "2025 é projeção geométrica institucional do INE, não recontagem censitária — selo “modelado”.",
    pop_aviso_moatize_limites:
      "O Distrito de Moatize mudou de limites administrativos entre censos: a comparabilidade entre 1997/2007/2017 NÃO é garantida.",
    pop_aviso_2017_naoajustado:
      "Os valores de 2017 são a contagem residente NÃO ajustada pela sub-enumeração estimada pelo INE — duas taxas de unidades diferentes, não uma faixa de incerteza de uma só grandeza: 3,7% a nível nacional (Moçambique); 3,8% na Província de Tete, unidade que aqui é pertinente para Cidade de Tete e Distrito de Moatize.",
    pop_aviso_total_nacional:
      "O total nacional publicado aqui é a soma dos ADM2 do COD-PS, e diverge do total do INE em +3 pessoas — leia o valor exato no CSV, não o digite.",
    // Molde com marcadores {piso} {teto} {desvioMin} {desvioMax} {desvioSemPeso} —
    // preenchidos em DemografiaPage.jsx a partir de
    // data/processed/populacao_vila_moatize_sensibilidade.csv, nunca escritos aqui.
    pop_aviso_vila_moatize:
      "A Vila de Moatize não tem contagem própria em fonte aberta: o valor de 2017 é o TETO de uma banda ({piso}–{teto}), estimado sobre a grade GRID3, não um valor central. A validação do mesmo método na Cidade de Tete mostrou que restringir a grade pela máscara de construído perde {desvioMin} a {desvioMax} das pessoas; só a soma sem peso validou ({desvioSemPeso}), e ela inclui área rural. Um único ano — sem série, sem CAGR. Ver docs/ADR/0017.",
    pop_indice_titulo: "Índice de crescimento (base = primeiro ano disponível de cada unidade)",
    pop_cagr_titulo: "CAGR por intervalo censitário",
    pop_ritmo_titulo: "Ritmo relativo — CAGR(unidade) ÷ CAGR(Moçambique)",
    pop_ritmo_metodo: "Razão simples entre o CAGR da unidade e o CAGR nacional no mesmo intervalo. Valor > 1: a unidade cresce mais rápido que o país nesse intervalo.",
    pop_tabela_titulo: "Tabela — unidade × ano",
    pop_moatize_vila_ausente_titulo: "Vila de Moatize",
    pop_moatize_vila_ausente_texto:
      "A vila-sede de Moatize (posto administrativo, nível ADM3) ainda não tem série própria neste CSV. O COD-PS (fonte A usada aqui) só publica população a nível ADM2 (distrito); a coleta complementar por WorldPop está em curso e pode não ter concluído nesta rodada. Esta linha permanece até o CSV trazer a unidade — não é omitida em silêncio.",
    pop_nivel_curto: "nível",

    // --- Componentes de ui.jsx e Como citar (Fase 4b, B1) ---
    ver_tabela: "Ver tabela",
    ver_grafico: "Ver gráfico",
    como_citar_titulo: "Como citar",
    como_citar_copiar: "Copiar referência",
    como_citar_copiado: "Copiado",
    como_citar_falhou: "Não foi possível copiar — selecione o texto manualmente.",
    como_citar_doi: "DOI",
    como_citar_autor: "Autor",
    como_citar_sem_doi:
      "Sem DOI ainda: o Zenodo emite o identificador na primeira release arquivada. Até lá, cite pela URL do painel.",
    rodape_versao: "Versão",
    rodape_licenca: "código MIT · dados CC BY 4.0",
    rodape_repositorio: "Repositório",

    // --- Página inicial (Fase 4b, B3): hero, KPIs, narrativa guiada, cartões Explore.
    // Nenhum número aqui: os valores vêm de narrativa.json via lib/marcadores.js.
    nav_inicio: "Início",
    inicio_numeros_kicker: "A história em {n} números",
    inicio_selo_observado: "observado",
    inicio_selo_interpolado: "interpolado",
    inicio_selo_modelado: "modelado",
    inicio_sparkline_sr: "Minigráfico da série de {ini} a {fim}; os valores estão nas abas de dados.",
    inicio_narrativa_aria: "Narrativa: o ciclo do carvão em Tete e Moatize, capítulo a capítulo",
    inicio_capitulos_aria: "Capítulos da narrativa",
    inicio_anterior: "anterior",
    inicio_proximo: "próximo",
    inicio_marcos_rotulo: "Marcos do período",
    inicio_marco_ausente: "marco não encontrado em marcos.json",
    inicio_nivel_b: "nível B — só validação (§4.0)",
    inicio_na_literatura: "Na literatura",
    inicio_explorar_ano: "Explorar {ano} no mapa →",
    inicio_mapa_rotulo: "Mapa de Tete e Moatize em {ano}: {titulo}",
    inicio_mapa_credito:
      "Vetores da classificação própria (Landsat/Sentinel-2) do ano do capítulo, sem imagem de satélite; troca de ano é corte entre classificações independentes, nunca interpolação (ADR 0013). Cores das classes: legenda ESA WorldCover, com adaptações declaradas (ADR 0018). Rodovias, ferrovia, aeródromo e topônimos: © OpenStreetMap (ODbL).",
    inicio_legenda_urbano: "mancha urbana orgânica",
    inicio_legenda_industrial: "pegada da mineração",
    inicio_legenda_reassentamento: "pegada de reassentamento",
    inicio_legenda_adensamento_2020_2025: "adensamento 2020→2025 (modelado)",
    inicio_legenda_varzea: "várzea",
    inicio_legenda_fantasma: "contorno urbano de {ano}",
    inicio_legenda_agua: "água (contexto)",
    inicio_mapa_carregando: "carregando camadas…",
    inicio_legenda_vias: "rodovias (contexto, OSM)",
    inicio_legenda_ferrovia: "ferrovia do Sena (contexto, OSM)",
    inicio_legenda_aerodromo: "aeródromo de Tete (contexto, OSM)",
    // Atribuição dos mapas (MapaTemporal, MapaNarrativa, Comparador) e legenda de cores (ADR 0018).
    mapa_atribuicao:
      "Tete–Moatize · classificação própria (Landsat/Sentinel-2) · data/processed/ · rodovias, ferrovia, aeródromo e topônimos: © OpenStreetMap contributors (ODbL)",
    mapa_temporal_aria: "Mapa temporal de Tete e Moatize",
    legenda_cores_worldcover: "Cores: legenda ESA WorldCover (FAO LCCS); adaptações declaradas",
    legenda_cores_adr: "ADR 0018 no repositório",
    legenda_adaptacao: "adaptação",
    legenda_oficial_tooltip: "Cor oficial da classe WorldCover {classe}.",
    legenda_adaptacao_tooltip: "Adaptação da classe WorldCover {classe}, não é cor oficial. {nota}",
    inicio_marcador_nao_declarado: "marcador não declarado no bloco",
    inicio_marcador_indisponivel: "valor indisponível: o dado de origem não pôde ser lido",
    inicio_explore_kicker: "Explore",
    inicio_explore_titulo: "Seções do painel",
    inicio_cartao_mancha_titulo: "Mancha e pegadas",
    inicio_cartao_mancha_desc:
      "Mapa por ano-âncora com as três camadas separadas — cidade, reassentamento e mineração —, comparação entre anos e estatísticas por núcleo.",
    inicio_cartao_provincia_titulo: "Província e cidades",
    inicio_cartao_provincia_desc:
      "Cidade de Tete, Moatize, a província e o país: população por censo, preço e produção de carvão, luz noturna e contas regionais.",
    inicio_cartao_populacao_titulo: "População",
    inicio_cartao_populacao_desc:
      "Séries censitárias por unidade, com selo de método e nível de fonte em cada ponto; projeções do INE marcadas como modeladas.",
    inicio_cartao_graficos_titulo: "Gráficos",
    inicio_cartao_graficos_desc:
      "Área urbana e luz noturna em índice, rosa e tipologia de expansão, comparação com as cidades-controle e o que o veredito causal não sustenta.",
    inicio_cartao_artigo_titulo: "Artigo",
    inicio_cartao_artigo_desc: "O manuscrito completo, com métodos, resultados, limitações e referências verificadas.",
    inicio_cartao_metodologia_titulo: "Metodologia",
    inicio_cartao_metodologia_desc:
      "Método por etapa, ambiente e versões gerados do lockfile, decisões metodológicas (ADR) e auditoria de dados.",
  },
  en: {
    titulo_app: "Tete–Moatize · urbanization and mining 1997–2025",
    nav_populacao: "Population",
    nav_graficos: "Charts",
    nav_artigo: "Article",
    nav_metodologia: "Methodology",
    ano: "Year",
    unidade: "Unit",
    camadas: "Layers",
    camada_urbano: "Urban (built-up)",
    camada_industrial: "Industrial/mining footprint",
    camada_reassentamento: "Resettlement footprint",
    camada_cultivo_irrigado: "Irrigated / flood-recession cropping",
    camada_cultivo_sequeiro: "Seasonal vegetation (not confirmed as cropland)",
    camada_agua: "Water",
    camada_varzea: "Floodplain (static)",
    camada_osm_vias: "Roads (N7 and others, OSM)",
    camada_osm_ferrovia: "Railway (Sena line, OSM)",
    camada_osm_lugares: "Place names (OSM)",
    camada_osm_aerodromo: "Tete aerodrome — TET/FQTT (OSM)",
    camada_adensamento_2020_2025: "Densification 2020→2025 (modeled, 3-signal agreement)",
    camada_adensamento_2020_2025_indisponivel: "available only in 2025 (2020→2025 contrast, modeled)",
    aviso_adensamento_selo:
      "MODELED layer (ADR 0016): synthesis of agreement between own classification, night-light trend (proxy of activity, NOT population), and building-footprint residual (Open Buildings, real window 2020→~2023, not 2020→2025). The “densifying” class cannot be added to “new expansion” — they are distinct answers.",
    aviso_adensamento_sensibilidade_prefixo: "Sensitivity to ±1 decile of cutoffs: ratio",
    aviso_adensamento_riscos:
      "The “densifying” area is NOT publishable as an exact number — only as spatial pattern and order of magnitude. The layer does not detect emptying/de-densification (the signal can only rise, by construction).",
    aviso_adensamento_sem_manifesto: "(full caveats unavailable — manifest.json not loaded)",
    aviso_urbano_comissao:
      "Warning: between 37% and 71% of what this map calls “urban” is not built-up — the commission error measured year by year (37.5% in 2025, 71.4% in 2010); see ADR 0009 and the re-run in ADR 0014. The layer can never decrease between years by construction (R2 ratchet, ADR 0013).",
    aviso_sequeiro:
      "Vegetation with strong seasonal phenology, NOT confirmed as cropland (measured user's accuracy = 0.000; ADR 0012).",
    nenhuma: "None",
    churn_titulo: "Instability between this year and the previous one",

    // --- Map and footprints (Phase 4b, B2): time slider, churn badge, comparator ---
    nav_mancha: "Built-up area and footprints",
    nav_provincia: "Province and towns",
    mapa_pagina_titulo: "Built-up area and footprints",
    mapa_modo_rotulo: "Display mode",
    mapa_modo_ano: "Single-year map",
    mapa_modo_comparar: "Compare two years",
    slider_ano_anterior: "Previous anchor year",
    slider_proximo_ano: "Next anchor year",
    slider_reproduzir: "Play",
    slider_pausar: "Pause",
    slider_movimento_reduzido: "Autoplay disabled — the system requests reduced motion (prefers-reduced-motion). Use ‹ and › to step manually.",
    slider_aria_label: "Anchor year shown on the map",
    slider_fora_do_intervalo: "outside the displayed scale, see arrow",
    slider_nivel_secundario: "secondary",
    slider_nivel_c: "level C — forbidden for a published number (§4.0)",
    marco_tipo_censo: "census",
    marco_tipo_concessao: "concession",
    marco_tipo_licenca: "license",
    marco_tipo_obras: "construction",
    marco_tipo_reassentamento: "resettlement",
    marco_tipo_operacao: "operation",
    marco_tipo_preco: "coal price",
    marco_tipo_logistica: "logistics",
    marco_tipo_saida: "exit/sale",
    comparar_ano_a: "Year A (left)",
    comparar_ano_b: "Year B (right)",
    comparar_sair: "Exit comparison",
    comparar_divisor: "Comparison divider",
    churn_primeiro_ano_ancora: "2000 — first anchor year, no previous pair",
    churn_sem_dado: "No churn recorded in the manifest for this year pair",
    churn_titulo_curto: "Classification instability between this anchor year and the previous one (built-up class)",
    churn_rotulo_curto: "Churn",
    churn_jaccard_rotulo: "Jaccard",
    churn_experimental_nota:
      "EXPERIMENTAL (ADR 0011/0013) — raw classifier label, before R1/R2 and the footprints; does not replace any published artifact. The year switch on the map is a discrete cut between independent classifications, never a continuous trajectory.",
    rodape_atribuicao_prefixo: "Sistema Ardósia (Ardósia design system) · data from",
    rodape_atribuicao_sufixo:
      "· no backend, no API key · own classification (Landsat/Sentinel-2), WSF Evolution (DLR), GHSL (JRC), COD-AB/COD-PS (HDX). No causal reading in this app is supported without the Phase 3 verdict alongside it.",
    baixar_dados: "Download data (CSV/GeoJSON) with citation",
    // --- Economic-context and milestone downloads (Phase 4b, B5) ---
    download_preco_carvao_rotulo: "Coal price — annual series (world market)",
    download_preco_carvao_citacao:
      "World Bank. Commodity Markets Observatory — CMO Historical Data Annual: Coal, Australian and Coal, South African (USD/mt, nominal). CC BY 4.0 license (see LICENSE-DADOS.md).",
    download_contas_regionais_rotulo: "Tete regional accounts (GDP, inflation)",
    download_contas_regionais_marca: "level C — context, not core",
    download_contas_regionais_citacao:
      "INE Mozambique, Tete Provincial Bulletin 2021, \"GDP and Inflation\" table (read via Wayback Machine snapshot; no license found on ine.gov.mz — level C, CLAUDE.md §4.0). Context only: does not support any core published number of this study.",
    download_producao_moatize_rotulo: "Coal production at Moatize (Vale) — annual series",
    download_producao_moatize_marca: "no published values yet",
    download_producao_moatize_citacao:
      "Vale S.A., Form 20-F (SEC EDGAR, CIK 0000917851), 2008–2022 — level A source, not yet accessed (pipeline/00_fetch/fetch_vale_20f.py awaits SEC_USER_AGENT configuration). Every row in this file is marked \"not available\": no value was invented (§4.0, §0).",
    download_marcos_rotulo: "Coal-cycle timeline milestones",
    download_marcos_citacao:
      "Vale S.A., Rio Tinto plc, Human Rights Watch, SEC EDGAR, INE — various institutional and regulatory documents. Bibliographic reference for each milestone in data/licenses_parts/marcos.md; source documents are not redistributed (see LICENSE-DADOS.md).",
    fonte: "Source",
    metodo: "Method",
    selo: "Stamp",
    ano_dado: "Data year",
    nivel: "Confidence level",
    fechar: "Close",
    veredito_causal_titulo: "Causal design verdict (Phase 3)",
    veredito_aviso:
      "All four tested breaks (2005, 2011, 2016, 2022) have an UNSUPPORTED or non-estimable counterfactual. No causal reading is supported by this study.",
    decomposicao_aviso:
      "The 2022 drop CANNOT be attributed to the mine (ADR 0015, decision 4). The decomposition is not a partition: floor and ceiling are published, never a single value.",
    aviso_ic_acuracia:
      "User accuracy carries a ±0.20 95% CI and the class covers 0.5–1.9 % of the AOI. None of the 15 anchor-year pairs has non-overlapping CIs: the variation across years (0.286 in 2010 to 0.625 in 2025) is NOT distinguishable from sampling noise. Read it as a single band for the whole series, never as improvement or decline over time (§10, ADR 0009).",
    piso_p_aviso:
      "Arithmetic floor of inference: with 1 treated unit and 5 donors, permutation inference has a minimum possible p = 1/6 ≈ 0.167 — no result in this study can reach conventional significance (p < 0.05), not because the effect is weak, but because of the arithmetic of the comparison pool. A p near 0.167 is the test's floor, not an ordinary null result: always read it together with the floor, never in isolation.",
    p_permutacao_titulo:
      "Permutation p-value (against the arithmetic floor of 1/6 ≈ 0.167; see warning above)",
    anel_periurbano_ausente:
      "Per-year periurban rings and a cropland→built-up transition mode do not yet exist in data/processed/ (§4.0: without the data, the app does not invent it). The spatial conversion logit is recorded as NOT DETERMINABLE in this round (causal/logit_conversao_status.csv): 31–54% churn between consecutive anchor years (ADR 0013) makes 'this pixel changed' a non-identifiable outcome without a stable origin class. The cropland layers below show each anchor year in isolation, never an inferred transition.",
    skip_link: "Skip to content",
    metod_ambiente_titulo: "Environment and libraries (§6-A.2)",
    metod_adr_titulo: "Methodological decisions — ADR (§6-A.5)",
    metod_provenance_titulo: "Provenance (PROVENANCE.md)",
    metod_audit_titulo: "Data audit (data/DATA_AUDIT.md)",
    kpi_demografia: "Demography / urban form",
    kpi_area_construida: "Built-up area (AOI)",
    kpi_pegada: "Industrial/resettlement footprint",
    kpi_agricultura: "Urban and periurban agriculture",
    kpi_acuracia: "Accuracy of the \"built-up\" class (ADR 0009)",
    kpi_sem_linhas: "No rows in stats_by_year_by_unit.csv for this unit/year.",
    veredicto_secao_titulo: "What the data does not support",

    // --- Population tab (demografia_serie_1997_2025.csv) ---
    pop_titulo: "Population — series by unit, 1997–2025",
    pop_aviso_titulo: "How to read these series",
    pop_aviso_niveis:
      "Every point has a source level A, B or C (§4.0); the level is in each value's tooltip. B/C-level points render with a hollow marker on the charts.",
    pop_aviso_2025:
      "2025 is an institutional geometric projection by INE, not a census recount — stamped “modeled”.",
    pop_aviso_moatize_limites:
      "Distrito de Moatize changed administrative boundaries between censuses: comparability across 1997/2007/2017 is NOT guaranteed.",
    pop_aviso_2017_naoajustado:
      "2017 values are the residents count NOT adjusted for the under-enumeration estimated by INE — two rates for two different units, not an uncertainty band on a single quantity: 3.7% nationally (Mozambique); 3.8% in Tete Province, the unit relevant here for Cidade de Tete and Distrito de Moatize.",
    pop_aviso_total_nacional:
      "The national total published here is the sum of COD-PS ADM2 units, and diverges from INE's total by +3 people — read the exact value from the CSV, do not type it.",
    // Template with markers {piso} {teto} {desvioMin} {desvioMax} {desvioSemPeso} —
    // filled in DemografiaPage.jsx from
    // data/processed/populacao_vila_moatize_sensibilidade.csv, never written here.
    pop_aviso_vila_moatize:
      "Moatize town has no count of its own in any open source: the 2017 figure is the CEILING of a band ({piso}–{teto}) estimated over the GRID3 grid, not a central value. Cross-validating the same method on Tete city showed that restricting the grid by a built-up mask loses {desvioMin} to {desvioMax} of the people; only the unweighted sum validated ({desvioSemPeso}), and it includes rural area. A single year — no series, no CAGR. See docs/ADR/0017.",
    pop_indice_titulo: "Growth index (base = first available year per unit)",
    pop_cagr_titulo: "CAGR by census interval",
    pop_ritmo_titulo: "Relative pace — CAGR(unit) ÷ CAGR(Mozambique)",
    pop_ritmo_metodo: "Simple ratio between the unit's CAGR and the national CAGR for the same interval. Value > 1: the unit grows faster than the country in that interval.",
    pop_tabela_titulo: "Table — unit × year",
    pop_moatize_vila_ausente_titulo: "Moatize town (vila)",
    pop_moatize_vila_ausente_texto:
      "The Moatize town seat (administrative post, ADM3 level) does not yet have its own series in this CSV. COD-PS (the level-A source used here) only publishes population at ADM2 (district) level; the complementary WorldPop collection is in progress and may not have finished this round. This row stays until the CSV brings the unit — it is never silently omitted.",
    pop_nivel_curto: "level",

    // --- ui.jsx components and "How to cite" (Phase 4b, B1) ---
    ver_tabela: "View table",
    ver_grafico: "View chart",
    como_citar_titulo: "How to cite",
    como_citar_copiar: "Copy reference",
    como_citar_copiado: "Copied",
    como_citar_falhou: "Could not copy — select the text manually.",
    como_citar_doi: "DOI",
    como_citar_autor: "Author",
    como_citar_sem_doi:
      "No DOI yet: Zenodo mints the identifier on the first archived release. Until then, cite the dashboard URL.",
    rodape_versao: "Version",
    rodape_licenca: "MIT code · CC BY 4.0 data",
    rodape_repositorio: "Repository",

    // --- Home page (Phase 4b, B3). No numbers here: values come from narrativa.json.
    nav_inicio: "Home",
    inicio_numeros_kicker: "The story in {n} numbers",
    inicio_selo_observado: "observed",
    inicio_selo_interpolado: "interpolated",
    inicio_selo_modelado: "modelled",
    inicio_sparkline_sr: "Sparkline of the series from {ini} to {fim}; the values are in the data tabs.",
    inicio_narrativa_aria: "Narrative: the coal cycle in Tete and Moatize, chapter by chapter",
    inicio_capitulos_aria: "Narrative chapters",
    inicio_anterior: "previous",
    inicio_proximo: "next",
    inicio_marcos_rotulo: "Milestones of the period",
    inicio_marco_ausente: "milestone not found in marcos.json",
    inicio_nivel_b: "level B — validation only (§4.0)",
    inicio_na_literatura: "In the literature",
    inicio_explorar_ano: "Explore {ano} on the map →",
    inicio_mapa_rotulo: "Map of Tete and Moatize in {ano}: {titulo}",
    inicio_mapa_credito:
      "Vectors from the own classification (Landsat/Sentinel-2) for the chapter's year, no satellite image; switching years is a cut between independent classifications, never interpolation (ADR 0013). Class colours: ESA WorldCover legend, with declared adaptations (ADR 0018). Roads, railway, airfield and place names: © OpenStreetMap (ODbL).",
    inicio_legenda_urbano: "organic urban footprint",
    inicio_legenda_industrial: "mining footprint",
    inicio_legenda_reassentamento: "resettlement footprint",
    inicio_legenda_adensamento_2020_2025: "densification 2020→2025 (modelled)",
    inicio_legenda_varzea: "floodplain",
    inicio_legenda_fantasma: "urban outline in {ano}",
    inicio_legenda_agua: "water (context)",
    inicio_mapa_carregando: "loading layers…",
    inicio_legenda_vias: "roads (context, OSM)",
    inicio_legenda_ferrovia: "Sena railway (context, OSM)",
    inicio_legenda_aerodromo: "Tete airfield (context, OSM)",
    mapa_atribuicao:
      "Tete–Moatize · own classification (Landsat/Sentinel-2) · data/processed/ · roads, railway, airfield and place names: © OpenStreetMap contributors (ODbL)",
    mapa_temporal_aria: "Time map of Tete and Moatize",
    legenda_cores_worldcover: "Colours: ESA WorldCover legend (FAO LCCS); adaptations declared",
    legenda_cores_adr: "ADR 0018 in the repository",
    legenda_adaptacao: "adaptation",
    legenda_oficial_tooltip: "Official colour of WorldCover class {classe}.",
    // A `nota` do YAML só existe em PT (config/paleta_uso_solo.yaml não tem `nota_en`): em EN a
    // dica declara a adaptação e aponta a justificativa, sem misturar PT na interface EN.
    legenda_adaptacao_tooltip:
      "Adaptation of WorldCover class {classe}, not an official colour. Rationale in ADR 0018.",
    inicio_marcador_nao_declarado: "marker not declared in the block",
    inicio_marcador_indisponivel: "value unavailable: the source data could not be read",
    inicio_explore_kicker: "Explore",
    inicio_explore_titulo: "Dashboard sections",
    inicio_cartao_mancha_titulo: "Built-up area and footprints",
    inicio_cartao_mancha_desc:
      "Map by anchor year with the three layers kept apart — city, resettlement and mining —, year comparison and statistics by core.",
    inicio_cartao_provincia_titulo: "Province and towns",
    inicio_cartao_provincia_desc:
      "Tete city, Moatize, the province and the country: population by census, coal price and output, night-light and regional accounts.",
    inicio_cartao_populacao_titulo: "Population",
    inicio_cartao_populacao_desc:
      "Census series by unit, with method stamp and source level on every point; INE projections marked as modelled.",
    inicio_cartao_graficos_titulo: "Charts",
    inicio_cartao_graficos_desc:
      "Urban area and night-light as an index, expansion rose and typology, comparison with the control cities and what the causal verdict does not support.",
    inicio_cartao_artigo_titulo: "Article",
    inicio_cartao_artigo_desc: "The full manuscript, with methods, results, limitations and verified references.",
    inicio_cartao_metodologia_titulo: "Methodology",
    inicio_cartao_metodologia_desc:
      "Method by stage, environment and versions generated from the lockfile, methodological decisions (ADR) and data audit.",
  },
};

export function I18nProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem("lang") || "pt");
  const t = useCallback((key) => DICIONARIO[lang]?.[key] ?? DICIONARIO.pt[key] ?? key, [lang]);
  const toggleLang = useCallback(() => {
    setLang((l) => {
      const novo = l === "pt" ? "en" : "pt";
      localStorage.setItem("lang", novo);
      return novo;
    });
  }, []);
  return (
    <I18nContext.Provider value={{ lang, t, toggleLang }}>{children}</I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n precisa de I18nProvider");
  return ctx;
}

// Divide um molde de i18n com marcadores "{chave}" em fragmentos alternados de texto
// e os nós React fornecidos em `partes[chave]` (ex.: um <ProvenanciaNumero>). Nunca
// formata número: só recorta a string em torno de valores já formatados por quem
// chama. Marcador sem parte correspondente é mantido literal (falha visível, não
// omissão silenciosa).
export function interpolarComPartes(molde, partes) {
  const regex = /\{(\w+)\}/g;
  const nos = [];
  let ultimo = 0;
  let m;
  let i = 0;
  while ((m = regex.exec(molde))) {
    if (m.index > ultimo) nos.push(molde.slice(ultimo, m.index));
    nos.push(
      Object.prototype.hasOwnProperty.call(partes, m[1]) ? (
        <span key={`${m[1]}-${i++}`}>{partes[m[1]]}</span>
      ) : (
        m[0]
      )
    );
    ultimo = regex.lastIndex;
  }
  if (ultimo < molde.length) nos.push(molde.slice(ultimo));
  return nos;
}
