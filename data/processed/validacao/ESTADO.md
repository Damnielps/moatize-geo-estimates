# Estado da validação de acurácia — Fase 1, concluída

`data/processed/acuracia_por_ano.csv` existe e cobre os seis anos-âncora.
Os 288 rótulos de referência foram produzidos e estão em
`rotulos_interpretados.csv`. O contrato
`test_acuracia_por_ano_csv_existe_e_tem_todos_os_anos` passa; a suíte fecha em
38/38.

## O que existe

| artefato | conteúdo |
|---|---|
| `pontos_validacao.csv` | 288 pontos (24 por estrato por ano), `id_ponto`, `id_cego`, estrato do mapa, linha/coluna, UTM |
| `chips/folha_<ano>_<nn>.png` | 24 folhas de contato, 12 pontos cada, duas janelas por ponto |
| `rotulos_interpretados.csv` | rótulo de referência por `id_cego`, com o intérprete identificado |
| `../acuracia_por_ano.csv` | AG, kappa, AU/AP de `construido`, todos com IC de 95 % |
| `../matriz_confusao_por_ano.csv` | matriz em contagem e em proporção de área |
| `../concordancia_wsf.csv` | concordância com o WSF, **rotulada como não-acurácia** |

## O que este número é, e o que não é

O intérprete é um **modelo de linguagem multimodal**, não um humano treinado e
não verdade de campo. **Não é fotointerpretação** e não é chamado assim. O erro
do intérprete entra no resultado como se fosse erro do mapa.

Duas decisões desta rodada, ambas correções de desenho:

1. **Cegamento.** Antes, `id_ponto` era atribuído depois de ordenar por estrato
   (001–024 sempre construído) e as folhas exibiam esse id em ordem — o
   intérprete saberia a classe do mapa antes de olhar o recorte, e a
   concordância mediria a pista. As folhas passam a exibir `id_cego`, de uma
   permutação determinística que mistura os estratos.
2. **Renderização.** O esticamento por percentis 2–98 **do próprio recorte,
   banda a banda**, decorrelacionava as bandas: o ruído independente de cada
   banda ganhava um ganho diferente e virava cor. Os recortes de 2000 saíam como
   mosaicos de pontos vermelhos, azuis e verdes sem relação com a superfície.
   Agora normaliza-se primeiro pelos percentis da AOI (preserva a relação entre
   bandas) e aplica-se **um único** ganho local, comum às três, calculado sobre
   a janela de contexto, com piso de amplitude para que recorte homogêneo saia
   homogêneo. Cada ponto ganhou também uma **janela de contexto de 3,0 km**, que
   a versão anterior não tinha.

## Resultado, sem maquiagem

- **Acurácia global 0,87–1,00**, acima da meta de §10 em todos os anos — mas a
  meta não discrimina aqui: o estrato `nao_construido` é 98–99,5 % da AOI, e um
  mapa que errasse toda a classe construída ainda teria AG ≈ 0,98.
- **Acurácia do usuário de `construido`: 0,27–0,63.** Comissão alta e
  consistente. É o número que importa e é o que reprova.
- **Acurácia do produtor não é utilizável neste n.** Um único ponto do estrato
  `nao_construido` carrega ~4,1 % da área da AOI no estimador.
- **Kappa 0,09–0,77**, abaixo da meta de 0,70 em 2010, 2015 e 2020.
- IC de 95 % da AG chega a **±0,133** (2020). Estreitá-lo a ±0,03 exigiria
  ~470 pontos por estrato por ano — ~2 800 recortes, inatingível por
  interpretação neste ambiente.

Leitura completa e o que seria preciso para melhorar: seção
`SECAO_ACURACIA` de `data/provenance_parts/imagem_fase1.md`.
