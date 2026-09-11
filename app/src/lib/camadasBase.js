// Base compartilhada do mapa MapLibre (§6, ADR 0013): estilo vazio, cores e estilos por
// camada e a adição do contexto OSM/várzea (vias, ferrovia, aeródromo, topônimos). Usada
// por MapaTemporal.jsx, pelos dois lados de Comparador.jsx e por MapaNarrativa.jsx — mesmas
// camadas, mesma ordem, mesmas cores nos três lugares.
import { Marker, AttributionControl } from "maplibre-gl";
import { carregarGeojson } from "./data.js";
// Paleta das classes de uso do solo: legenda ESA WorldCover (FAO LCCS) com adaptações
// declaradas (docs/ADR/0018). GERADA de config/paleta_uso_solo.yaml por
// pipeline/05_app/gerar_paleta.py — nenhuma cor de classe é escrita à mão neste app. A
// identidade Ardósia continua em todo o resto da interface (cabeçalho, tipografia, gráficos
// que não são classes de uso do solo).
import paleta from "../content/paleta_uso_solo.json";

export const PALETA = paleta;
const CLASSES = paleta.classes;
const CONTEXTO = paleta.contexto;

export const CORES_CAMADA = {
  urbano: CLASSES.urbano.cor,
  industrial: CLASSES.industrial.cor,
  reassentamento: CLASSES.reassentamento.cor,
  cultivo_irrigado: CLASSES.cultivo_irrigado.cor,
  cultivo_sequeiro: CLASSES.cultivo_sequeiro.cor,
  agua: CLASSES.agua.cor,
  varzea: CLASSES.varzea.cor,
  adensamento_2020_2025: CLASSES.adensamento_2020_2025.cor,
  // Contexto OSM (ODbL): cinzas neutros da seção `contexto`, fora da legenda de uso do solo.
  osm_vias: CONTEXTO.vias,
  osm_ferrovia: CONTEXTO.ferrovia,
  osm_aerodromo: CONTEXTO.aerodromo,
  osm_lugares: CONTEXTO.toponimo,
};

/** Contorno das classes adaptadas que o exigem (reassentamento e industrial, ADR 0018). */
export const CONTORNO_CAMADA = {
  reassentamento: CLASSES.reassentamento.contorno,
  industrial: CLASSES.industrial.contorno,
};
export const COR_FUNDO_MAPA = CONTEXTO.fundo_mapa;
export const COR_CONTORNO_FANTASMA = CONTEXTO.contorno_fantasma;
export const OPACIDADE_VARZEA = CLASSES.varzea.opacidade;
// Opacidade do preenchimento das classes medidas: alta o bastante para a cor ler como a da
// legenda WorldCover sobre o fundo branco, baixa o bastante para o contexto OSM (por cima)
// e a várzea (por baixo) continuarem legíveis.
export const OPACIDADE_CLASSE = 0.75;

/** Metadados de legenda da classe (origem, nota, classe WorldCover), ou null (contexto OSM). */
export function metaClasse(camada) {
  return CLASSES[camada] ?? null;
}

/** `#RRGGBB` + alfa em [0, 1] -> `rgba(...)` (amostras de legenda com a opacidade do mapa). */
export function comAlfa(hex, alfa) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alfa})`;
}

/**
 * Estilo CSS da amostra de legenda de uma camada, espelhando o desenho no mapa: contorno
 * nas classes que o têm, só tracejado no sequeiro, hachura no adensamento modelado, linha
 * nas vias e na ferrovia. Usado por PainelCamadas.jsx e MapaNarrativa.jsx.
 */
export function estiloAmostra(camada) {
  const cor = CORES_CAMADA[camada];
  switch (camada) {
    case "reassentamento":
    case "industrial":
      return { background: comAlfa(cor, OPACIDADE_CLASSE), border: `1.5px solid ${CONTORNO_CAMADA[camada]}` };
    case "cultivo_sequeiro":
      return { background: "transparent", border: `1.5px dashed ${cor}` };
    case "varzea":
      return { background: comAlfa(cor, OPACIDADE_VARZEA), border: `1px solid ${comAlfa(cor, 0.5)}` };
    case "adensamento_2020_2025":
      return {
        background: `repeating-linear-gradient(135deg, ${cor} 0 1.5px, transparent 1.5px 4px)`,
        border: `1px dashed ${cor}`,
      };
    case "osm_vias":
      return { background: `linear-gradient(transparent 40%, ${cor} 40% 62%, transparent 62%)`, border: "none" };
    case "osm_ferrovia":
      return {
        background: `repeating-linear-gradient(90deg, ${cor} 0 3px, transparent 3px 5px) center / 100% 2px no-repeat`,
        border: "none",
      };
    case "osm_lugares":
      return { background: `radial-gradient(circle, ${cor} 0 2.5px, transparent 3px)`, border: "none" };
    case "osm_aerodromo":
      return { background: comAlfa(cor, 0.35), border: `1px solid ${cor}` };
    default:
      return { background: comAlfa(cor, OPACIDADE_CLASSE), border: "1px solid rgba(0, 0, 0, 0.12)" };
  }
}

// Camadas que só existem num ano exibido. `adensamento_2020_2025` é um CONTRASTE
// 2020→2025 MODELADO (concordância de três sinais, ADR 0016): desenhá-la sobre 2000,
// 2005, 2010 ou 2015 — e, com o play, animá-la por esses anos — sugeriria adensamento
// onde o estudo não estima nada (§0: observado ≠ modelado). Só é desenhada quando o ano
// exibido é 2025; fora dele o painel desabilita o checkbox com nota bilíngue.
export const ANO_EXCLUSIVO_CAMADA = { adensamento_2020_2025: 2025 };

export function camadaDisponivelNoAno(camada, ano) {
  const exclusivo = ANO_EXCLUSIVO_CAMADA[camada];
  return exclusivo == null || exclusivo === ano;
}

/** Visibilidade efetiva: ligada no painel E disponível no ano exibido. */
export function camadaVisivel(camada, camadasAtivas, ano) {
  return !!camadasAtivas[camada] && camadaDisponivelNoAno(camada, ano);
}

// Classifica um `place` do OSM em uma classe de tamanho de rótulo (city > town >
// village > suburb/hamlet), conforme a tarefa de contexto (topônimos/vias/ferrovia).
export function classeDeLugar(place) {
  if (place === "city") return "city";
  if (place === "town") return "town";
  if (place === "village") return "village";
  return "pequeno"; // suburb, neighbourhood, hamlet, etc.
}

// Mapa de nome de camada (chave de `camadasAtivas`) para o(s) id(s) de layer MapLibre. A
// maioria é `layer-<camada>`; `varzea` e o contexto OSM têm ids próprios, e uma camada da
// interface pode ser MAIS DE UMA camada do MapLibre: o aeródromo (área e pista) e as classes
// com contorno (ADR 0018: reassentamento, industrial, adensamento). Alternar só a primeira
// deixaria a outra visível com a camada desligada no painel.
export const ID_LAYER_POR_CAMADA = {
  varzea: "varzea-fill",
  osm_vias: "layer-osm-vias",
  osm_ferrovia: "layer-osm-ferrovia",
  osm_aerodromo: "layer-osm-aerodromo-area",
};
const IDS_EXTRAS = {
  osm_aerodromo: ["layer-osm-aerodromo-pista"],
  reassentamento: ["layer-reassentamento-contorno"],
  industrial: ["layer-industrial-contorno"],
  adensamento_2020_2025: ["layer-adensamento_2020_2025-contorno"],
};

/** Todos os ids de layer MapLibre de uma camada da interface. */
export function idsDaCamada(camada) {
  return [ID_LAYER_POR_CAMADA[camada] ?? `layer-${camada}`, ...(IDS_EXTRAS[camada] ?? [])];
}

// Ordem de pintura FIXA (de baixo para cima). As fontes chegam por fetch assíncrono e
// em ordem imprevisível (cache, rede, ano trocado no meio); sem ordem declarada, a pilha
// dependia de quem respondia primeiro — num carregamento as vias ficavam sob a mancha,
// noutro sobre ela. Cada camada é inserida antes da primeira camada POSTERIOR a ela
// nesta lista que já exista no mapa, então o resultado é o mesmo em qualquer ordem de
// chegada. Contexto OSM por cima (referência de leitura sobre as manchas medidas).
export const ORDEM_CAMADAS = [
  "fundo",
  "varzea-fill",
  // Abaixo das camadas classificadas: em 2025 a mancha medida continua legível por cima da
  // síntese MODELADA (hachura), em vez de ser recoberta por ela.
  "layer-adensamento_2020_2025",
  "layer-adensamento_2020_2025-contorno",
  "layer-agua",
  "layer-urbano",
  "layer-industrial",
  "layer-industrial-contorno",
  "layer-reassentamento",
  "layer-reassentamento-contorno",
  "layer-cultivo_irrigado",
  "layer-cultivo_sequeiro",
  "layer-osm-aerodromo-area",
  "layer-osm-vias",
  "layer-osm-ferrovia",
  "layer-osm-aerodromo-pista",
];

/**
 * Controle de atribuição com texto do idioma corrente (i18n `mapa_atribuicao`). O MapLibre
 * não troca `customAttribution` de um controle existente: a troca de idioma remove o
 * anterior e adiciona outro. Devolve a função de remoção, para o `cleanup` do efeito.
 */
export function montarAtribuicao(map, texto, posicao = "bottom-right") {
  const controle = new AttributionControl({ customAttribution: texto });
  map.addControl(controle, posicao);
  return () => {
    if (mapaUtilizavel(map)) map.removeControl(controle);
  };
}

/** `map.addLayer` na posição de ORDEM_CAMADAS, independente da ordem de chegada. */
export function adicionarNaOrdem(map, especificacao) {
  const i = ORDEM_CAMADAS.indexOf(especificacao.id);
  const antes = i < 0 ? undefined : ORDEM_CAMADAS.slice(i + 1).find((id) => map.getLayer(id));
  map.addLayer(especificacao, antes);
}

/**
 * Um mapa removido (`map.remove()`) não aceita fonte nova, e um mapa cujo evento `load`
 * ainda não disparou lança "Style is not done loading" em `addSource`. Quem chama só
 * entrega aqui o mapa depois do `load` (MapaTemporal/Comparador guardam a INSTÂNCIA
 * carregada, não um booleano); esta checagem cobre a resposta que chega depois da
 * desmontagem.
 */
export function mapaUtilizavel(map) {
  return !!map && !map._removed && !!map.style;
}

export const CAMADAS_POR_ANO = ["agua", "urbano", "industrial", "reassentamento", "cultivo_irrigado", "cultivo_sequeiro"];

/**
 * Especificações MapLibre de uma classe por ano (ADR 0018): preenchimento WorldCover,
 * contorno nas adaptações que o exigem, e só contorno tracejado no sequeiro (candidata
 * reprovada na validação, ADR 0012 — não recebe o preenchimento de Cropland).
 */
function especificacoesDaClasse(camada, srcId, visibilidade) {
  const layout = { visibility: visibilidade };
  const cor = CORES_CAMADA[camada];
  if (camada === "cultivo_sequeiro") {
    return [
      {
        id: `layer-${camada}`,
        type: "line",
        source: srcId,
        layout,
        paint: { "line-color": cor, "line-width": 1.1, "line-dasharray": [2, 1.5], "line-opacity": 0.95 },
      },
    ];
  }
  const especs = [
    {
      id: `layer-${camada}`,
      type: "fill",
      source: srcId,
      layout,
      paint: { "fill-color": cor, "fill-opacity": OPACIDADE_CLASSE },
    },
  ];
  if (CONTORNO_CAMADA[camada]) {
    especs.push({
      id: `layer-${camada}-contorno`,
      type: "line",
      source: srcId,
      layout,
      paint: { "line-color": CONTORNO_CAMADA[camada], "line-width": 1.2 },
    });
  }
  return especs;
}

/**
 * Carrega as camadas classificadas de `ano` (por padrão as seis de CAMADAS_POR_ANO) e as
 * aplica ao mapa DE UMA VEZ, só se a requisição ainda for a vigente (`vigente()` falso =
 * outro ano foi pedido depois, ou o componente desmontou). As camadas pedidas chegam em
 * paralelo; nenhuma é aplicada antes de todas chegarem, então o mapa nunca mistura camadas
 * de dois anos, e uma resposta atrasada de um ano anterior nunca sobrescreve a do ano
 * corrente (era a corrida do carregamento a frio: fontes de um ano obsoleto aplicadas depois
 * das do ano exibido).
 *
 * `camadas` restringe o conjunto: o mapa da narrativa pede só as que o capítulo mostra.
 * Pedir as seis ali fazia o passo esperar pelos GeoJSON de cultivo (2–6 MB por ano) que a
 * home nunca desenha — a aplicação inteira ficava refém do arquivo mais pesado.
 * `visivel(camada)` é consultada NA HORA de criar a camada (estado corrente do painel).
 */
export async function aplicarCamadasDoAno(map, ano, visivel, vigente, camadas = CAMADAS_POR_ANO) {
  const lista = CAMADAS_POR_ANO.filter((c) => camadas.includes(c));
  const dados = await Promise.all(lista.map((camada) => carregarGeojson(camada, ano)));
  if (!vigente() || !mapaUtilizavel(map)) return false;
  lista.forEach((camada, i) => {
    const srcId = `src-${camada}`;
    const fonte = map.getSource(srcId);
    if (fonte) {
      fonte.setData(dados[i]);
    } else {
      map.addSource(srcId, { type: "geojson", data: dados[i] });
    }
    const visibilidade = visivel(camada) ? "visible" : "none";
    for (const espec of especificacoesDaClasse(camada, srcId, visibilidade)) {
      if (!map.getLayer(espec.id)) adicionarNaOrdem(map, espec);
    }
  });
  return true;
}

/**
 * Estilo MapLibre vazio (sem tile de terceiros, sem chave de API): só o fundo
 * (`contexto.fundo_mapa` da paleta, ADR 0018). `glyphs` é OMITIDO, não definido como undefined — o validador de estilo
 * do MapLibre trata a chave presente-com-undefined como valor inválido ("glyphs:
 * string expected, undefined found") e o erro impede o evento `load` de disparar,
 * deixando o mapa em branco sem erro visível na tela. Sem `glyphs` não há rótulo de
 * texto, o que é intencional: os topônimos são `Marker` de DOM (ver
 * `adicionarContextoOsm`), não uma camada `symbol`.
 *
 * Função (não constante) para que cada mapa (MapaTemporal, e os dois lados de
 * Comparador) receba seu próprio objeto — o MapLibre pode anexar estado interno ao
 * objeto de estilo, e compartilhar a mesma referência entre dois mapas é frágil.
 */
export function criarEstiloVazio() {
  return {
    version: 8,
    sources: {},
    layers: [
      { id: "fundo", type: "background", paint: { "background-color": COR_FUNDO_MAPA } },
    ],
  };
}

/**
 * Adiciona a camada estática da várzea (fill), se ainda não existir no mapa.
 * Idêntica em todos os anos-âncora — carregada uma vez por instância de mapa.
 * `visivelAgora()` lida depois do fetch (estado corrente do painel, não o do disparo).
 */
export async function adicionarCamadaVarzea(map, visivelAgora, cancelado = () => false) {
  if (map.getSource("varzea")) return;
  const gj = await carregarGeojson("varzea", null);
  if (cancelado() || !mapaUtilizavel(map) || map.getSource("varzea")) return;
  map.addSource("varzea", { type: "geojson", data: gj });
  adicionarNaOrdem(map, {
    id: "varzea-fill",
    type: "fill",
    source: "varzea",
    layout: { visibility: visivelAgora() ? "visible" : "none" },
    // Zona modelada, não cobertura: cor de Herbaceous wetland na opacidade do YAML.
    paint: { "fill-color": CORES_CAMADA.varzea, "fill-opacity": OPACIDADE_VARZEA },
  });
}

// Hachuras do adensamento (ADR 0018: camada MODELADA nunca com o preenchimento sólido da
// mancha observada). Geradas em canvas, uma vez por mapa (`addImage`), na cor da classe.
const HACHURAS = {
  "hachura-adensando": { cor: () => CORES_CAMADA.adensamento_2020_2025, passo: 6, espessura: 1.6, sentido: 1 },
  "hachura-expansao-nova": { cor: () => CORES_CAMADA.adensamento_2020_2025, passo: 10, espessura: 1.4, sentido: -1 },
  // Pegada industrial dentro do contraste: cinza do contorno industrial, nunca vermelho (§10).
  "hachura-pegada-industrial": { cor: () => CONTORNO_CAMADA.industrial, passo: 8, espessura: 1.2, sentido: 1 },
};

function imagemHachura({ cor, passo, espessura, sentido }) {
  const pr = 2; // desenhada em 2x para não serrilhar em tela de alta densidade
  const lado = passo * pr;
  const canvas = document.createElement("canvas");
  canvas.width = lado;
  canvas.height = lado;
  const ctx = canvas.getContext("2d");
  ctx.strokeStyle = cor();
  ctx.lineWidth = espessura * pr;
  ctx.lineCap = "square";
  ctx.beginPath();
  // Três diagonais (a central e as duas das bordas) para o padrão emendar sem costura.
  for (const d of [-lado, 0, lado]) {
    if (sentido > 0) {
      ctx.moveTo(d, lado);
      ctx.lineTo(d + lado, 0);
    } else {
      ctx.moveTo(d, 0);
      ctx.lineTo(d + lado, lado);
    }
  }
  ctx.stroke();
  return { imagem: ctx.getImageData(0, 0, lado, lado), pixelRatio: pr };
}

function registrarHachuras(map) {
  for (const [id, def] of Object.entries(HACHURAS)) {
    if (map.hasImage(id)) continue;
    const { imagem, pixelRatio } = imagemHachura(def);
    map.addImage(id, imagem, { pixelRatio });
  }
}

/**
 * Adiciona a camada MODELADA `adensamento_2020_2025` (ADR 0016), se ainda não existir.
 * Síntese única do intervalo 2020→2025 (GeoJSON sem sufixo de ano), categórica por
 * `classe`. Desenho (ADR 0018): hachura densa em `adensando`, hachura aberta no sentido
 * oposto em `expansao_nova`, hachura cinza em `pegada_industrial`, e só contorno tracejado
 * (fraco) em `consolidado`/`esparso_estavel` — nenhum preenchimento sólido.
 * `visivelAgora()` é consultada só depois do carregamento — quem chama passa
 * `camadaVisivel(...)` sobre o estado corrente, para a camada nascer oculta quando o ano
 * exibido não é 2025. `cancelado()` evita adicionar a um mapa já desmontado.
 * Usada por MapaTemporal.jsx, pelos dois lados de Comparador.jsx e por MapaNarrativa.jsx.
 */
export async function adicionarCamadaAdensamento(map, visivelAgora, cancelado = () => false) {
  if (map.getSource("adensamento_2020_2025")) return;
  const gj = await carregarGeojson("adensamento_2020_2025", null);
  if (cancelado() || !mapaUtilizavel(map) || map.getSource("adensamento_2020_2025")) return;
  registrarHachuras(map);
  map.addSource("adensamento_2020_2025", { type: "geojson", data: gj });
  const visibility = visivelAgora() ? "visible" : "none";
  const cor = CORES_CAMADA.adensamento_2020_2025;
  adicionarNaOrdem(map, {
    id: "layer-adensamento_2020_2025",
    type: "fill",
    source: "adensamento_2020_2025",
    filter: ["in", ["get", "classe"], ["literal", ["adensando", "expansao_nova", "pegada_industrial"]]],
    layout: { visibility },
    paint: {
      "fill-pattern": [
        "match",
        ["get", "classe"],
        "adensando", "hachura-adensando",
        "expansao_nova", "hachura-expansao-nova",
        "hachura-pegada-industrial",
      ],
    },
  });
  adicionarNaOrdem(map, {
    id: "layer-adensamento_2020_2025-contorno",
    type: "line",
    source: "adensamento_2020_2025",
    layout: { visibility },
    paint: {
      "line-color": ["match", ["get", "classe"], "pegada_industrial", CONTORNO_CAMADA.industrial, cor],
      "line-width": 0.9,
      "line-dasharray": [2, 1.5],
      "line-opacity": ["match", ["get", "classe"], ["adensando", "expansao_nova"], 0.9, 0.45],
    },
  });
}

/**
 * Adiciona as camadas de contexto OpenStreetMap (ODbL, nível A) — vias, ferrovia,
 * aeródromo (área + pista) e topônimos (Marker de DOM) — e retorna a lista de
 * `{ marker, place }` criada para os topônimos, para quem chamou controlar
 * visibilidade por zoom/toggle (ex.: `aplicarVisibilidadeRotulos` em
 * MapaTemporal.jsx). Devolve `null` — sem criar nada — se o contexto já existir neste
 * mapa (idempotente), se o mapa foi removido ou se `cancelado()` for verdadeiro quando
 * os dados chegarem. `lerCamadasAtivas()` é lida depois do fetch.
 */
export async function adicionarContextoOsm(map, lerCamadasAtivas, cancelado = () => false) {
  const [vias, ferrovia, lugares, aerodromo] = await Promise.all([
    carregarGeojson("osm_vias", null),
    carregarGeojson("osm_ferrovia", null),
    carregarGeojson("osm_lugares", null),
    carregarGeojson("osm_aerodromo", null),
  ]);
  // Desmontado (ou outro disparo já adicionou): nada a fazer — e, sobretudo, nenhum
  // Marker de DOM criado sobre um mapa que não existe mais.
  if (cancelado() || !mapaUtilizavel(map) || map.getSource("osm-vias")) return null;
  // Estado do painel lido DEPOIS do fetch, não no disparo.
  const camadasAtivas = lerCamadasAtivas();

  if (!map.getSource("osm-vias")) {
    map.addSource("osm-vias", { type: "geojson", data: vias });
    adicionarNaOrdem(map, {
      id: "layer-osm-vias",
      type: "line",
      source: "osm-vias",
      layout: {
        visibility: camadasAtivas.osm_vias ? "visible" : "none",
        "line-cap": "round",
        "line-join": "round",
      },
      paint: {
        "line-color": CORES_CAMADA.osm_vias,
        // Espessura por classe funcional: trunk (N7 — eixo Tete–Moatize) > primary
        // > secondary > tertiary, para a N7 permanecer legível mesmo com muitas
        // vias terciárias na mesma área.
        "line-width": [
          "match",
          ["get", "highway"],
          "trunk", 3.2,
          "primary", 2.4,
          "secondary", 1.7,
          "tertiary", 1.1,
          1,
        ],
      },
    });
  }

  if (!map.getSource("osm-ferrovia")) {
    map.addSource("osm-ferrovia", { type: "geojson", data: ferrovia });
    adicionarNaOrdem(map, {
      id: "layer-osm-ferrovia",
      type: "line",
      source: "osm-ferrovia",
      layout: {
        visibility: camadasAtivas.osm_ferrovia ? "visible" : "none",
      },
      paint: {
        // Tracejada e de cor distinta das rodovias — é a linha do Sena, relevante
        // ao corredor logístico do estudo (§1), não apenas contexto genérico.
        "line-color": CORES_CAMADA.osm_ferrovia,
        "line-width": 1.8,
        "line-dasharray": [2, 1.6],
      },
    });
  }

  // Aeródromo de Tete / Chingodzi (IATA TET, ICAO FQTT). Duas geometrias no mesmo
  // arquivo: o POLÍGONO do sítio aeroportuário e a LINHA da pista 01/19. São
  // desenhados separadamente porque comunicam coisas diferentes — a área é uso do
  // solo (e compete visualmente com `urbano` e `industrial` ao redor), a pista é a
  // infraestrutura em si. Filtrar por `aeroway` no mesmo source evita um segundo
  // fetch e mantém a proveniência num arquivo só.
  if (!map.getSource("osm-aerodromo")) {
    map.addSource("osm-aerodromo", { type: "geojson", data: aerodromo });
    const visivel = camadasAtivas.osm_aerodromo ? "visible" : "none";
    adicionarNaOrdem(map, {
      id: "layer-osm-aerodromo-area",
      type: "fill",
      source: "osm-aerodromo",
      filter: ["==", ["get", "aeroway"], "aerodrome"],
      layout: { visibility: visivel },
      paint: {
        "fill-color": CORES_CAMADA.osm_aerodromo,
        // Opacidade baixa: é contexto, não pode competir com as camadas medidas.
        "fill-opacity": 0.18,
        "fill-outline-color": CORES_CAMADA.osm_aerodromo,
      },
    });
    adicionarNaOrdem(map, {
      id: "layer-osm-aerodromo-pista",
      type: "line",
      source: "osm-aerodromo",
      filter: ["==", ["get", "aeroway"], "runway"],
      layout: { visibility: visivel, "line-cap": "butt" },
      paint: { "line-color": CORES_CAMADA.osm_aerodromo, "line-width": 3 },
    });
  }

  const marcadores = [];
  for (const feat of lugares.features || []) {
    const props = feat.properties || {};
    const [lng, lat] = feat.geometry.coordinates;
    const place = classeDeLugar(props.place);
    const el = document.createElement("div");
    el.className = `mapa-rotulo mapa-rotulo--${place}`;
    el.style.setProperty("--cor-toponimo", CORES_CAMADA.osm_lugares);
    el.textContent = props.name || "";
    const marker = new Marker({ element: el, anchor: "left", offset: [4, 0] })
      .setLngLat([lng, lat])
      .addTo(map);
    marcadores.push({ marker, place });
  }
  return marcadores;
}
