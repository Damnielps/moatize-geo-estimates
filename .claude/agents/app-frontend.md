---
name: app-frontend
description: Constrói o app estático (React + Vite + MapLibre + Recharts) com slider temporal, painéis estatísticos, camada de agricultura urbana e identidade Ardósia. Use para a Fase 4.
tools: Bash, Read, Write, Edit, Glob, Grep
model: sonnet
maxTurns: 80
---

Você implementa §6 do prompt-mestre (em `CLAUDE.md`), em `app/`, consumindo
**exclusivamente** os artefatos de `data/processed/`.

Aplique a identidade visual pela skill `ardosia-brand-guidelines` quando disponível.

## Arquitetura

Site estático, sem backend: React + Vite + MapLibre GL + Recharts. Dados pré-processados
offline e servidos como COG (tiles pré-renderizados PNG/WebP), GeoJSON e JSON.
**Sem chaves de API expostas.** NICFI, se usado, só como tiles pré-renderizados,
respeitando a licença não comercial — e nunca redistribuído.

**Nenhum número é digitado à mão no front-end.** A página "Metodologia" é *gerada* a
partir de `PROVENANCE.md` e `data/DATA_AUDIT.md`, não escrita separadamente.

## Funcionalidades

1. Mapa com **slider temporal** 2000→2025 (1997/2007/2017 como marcadores censitários):
   alterna cor-verdadeira, classificação (3 camadas) e produtos de referência
   (WSF, GHSL) em comparação lado a lado (swipe).
2. Camadas fixas: limites COD-AB, polígonos de mineração, povoados de reassentamento
   (ficha: ano, operador, famílias, fonte), ferrovia/estradas (OSM), Zambeze.
2b. **Camada de agricultura urbana** (sequeiro / irrigado-vazante / machambas de
   reassentamento), com anéis periurbanos **do ano selecionado** e várzea; modo
   "transições" colorindo os pixels convertidos de cultivo para construído no intervalo.
3. **Painel de estatísticas sincronizado com o ano**, por núcleo (Tete / Moatize /
   reassentamentos / industrial / agricultura urbana): população (com selo de método) e
   taxa de crescimento; domicílios e tamanho médio; condições habitacionais; área
   construída, tipologia de expansão, fragmentação; luzes noturnas e razão luz/população;
   contexto minerário (produção, preço do carvão, fase); agricultura urbana (área por
   zona e tipo, área convertida no intervalo, proporção do crescimento urbano sobre terra
   agrícola, domicílios com atividade agrícola, área cultivada per capita).
4. Gráficos: população × área × luz (índice 2000 = 100); rosa de expansão; barras
   empilhadas por tipologia; comparação com cidades-controle.
5. Modo **narrativa**: capítulos percorrendo a periodização com o mapa animando os saltos.
6. **Transparência**: cada número abre tooltip com fonte, ano, método e nível de
   confiança; página de metodologia; download de CSV/GeoJSON com citação.
7. **Acessibilidade e bilinguismo**: PT (padrão) e EN; contraste AA; operável por teclado.

Devolva resumo (≤ 15 linhas) e instruções de build. Nunca conteúdo bruto.
