# ADR 0007 — Validação por interpretação visual, n pequeno e declarado

**Data:** 2026-09-07
**Estado:** aceito
**Contexto:** escalonamento T2→T3; a validação da classificação foi reprovada.

## Problema

A versão anterior reportava acurácia global de 0,73–0,82 sobre 300 pontos/ano.
Os rótulos de referência desses pontos vinham de uma **segunda regra espectral**
aplicada à mesma imagem. Isso mede concordância entre duas regras sobre um sinal
que ambas confundem (solo exposto × construído na savana semiárida em estação
seca) — não mede acurácia. §5.1 e §10 pedem pontos fotointerpretados.

## Decisão

1. Os pontos passam a ser rotulados por **interpretação visual de recortes RGB**
   (composição SWIR1/NIR/vermelho, janela de 31 px × 30 m), um a um.
2. O intérprete é **um modelo de linguagem multimodal**, não um humano e não
   verdade de campo. Isso está declarado em todos os artefatos e **não é chamado
   de fotointerpretação**, que pressupõe intérprete humano treinado.
3. `n_pontos_validacao_por_ano: 300` é substituído por
   `n_pontos_interpretados_por_estrato_ano: 24` (48 por ano, 288 no total).
4. A amostra é **estratificada pelo mapa** (construído × não construído) e a
   acurácia global é recuperada pelo estimador de Olofsson et al. (2014),
   ponderado pela área de cada estrato, com intervalo de confiança de 95%.

## Motivo do n menor

Cada ponto exige olhar um recorte. 288 recortes é o que se interpreta com
atenção nesta tarefa. O preço é um intervalo de confiança largo, que é
**reportado**, não escondido. A alternativa — manter n = 300/ano por regra
automática — produz um número preciso e sem significado.

## Consequência

`data/processed/acuracia_por_ano.csv` passa a trazer acurácia com IC, acurácia
do produtor e do usuário por classe, e a marca explícita do tipo de intérprete.
A comparação com a meta de §10 (≥ 0,85) é reportada com o número real.

---

## Emenda (execução da validação)

Duas correções de desenho feitas ao executar o que este ADR decidiu. Nenhuma
altera a decisão; ambas corrigem defeitos que a tornariam vazia.

### 1. O intérprete passa a ser cego ao mapa

`id_ponto` é atribuído **depois** de ordenar os pontos por estrato: 001–024 são
sempre `construido` e 025–048 sempre `nao_construido`. As folhas de contato
exibiam esse identificador, em ordem, e cada folha continha um único estrato.
O intérprete saberia a classe do mapa antes de olhar o recorte, e a concordância
medida ficaria inflada por essa pista — o mesmo tipo de vício que reprovou a
versão anterior, por outra porta.

Cada ponto recebe agora um segundo identificador, `id_cego`, atribuído sobre uma
permutação determinística que mistura os dois estratos. As folhas exibem só
`id_cego`; o vínculo com o estrato existe apenas no CSV. `acuracia.py` faz o
join por `id_cego`.

### 2. O realce por recorte, banda a banda, era ilegível

O ADR previa "contraste por percentis 2–98 do próprio recorte". Medido na
execução: esticar **cada banda** contra o próprio intervalo local
**decorrelaciona as bandas**. O ruído independente de cada banda recebe um ganho
diferente e vira cor. Nos recortes de 2000 (mediana de 3 observações por pixel,
ADR 0008) o resultado é um mosaico de pontos vermelhos, azuis e verdes sem
relação com a superfície, sobre o qual não se rotula nada.

Adotado: normalizar primeiro pelos percentis 2–98 **da AOI** — o que preserva a
relação entre bandas e, portanto, a cor do alvo — e só então aplicar **um único**
ganho linear local, comum às três bandas. Ruído correlacionado continua cinza; o
que ganha contraste é a estrutura. Um piso de amplitude impede que um recorte
espectralmente homogêneo tenha o ruído esticado até parecer estruturado.

### 3. Duas janelas por ponto

Acrescentada uma janela de **contexto de 3,0 km** ao lado do detalhe de 0,9 km.
A decisão "este pixel é construído" a 30 m depende de padrão de ocupação — estar
dentro de uma malha, na borda de um povoado ou isolado no mato muda o julgamento,
e 0,9 km não mostra isso. Nenhuma das duas janelas expõe variável do
classificador. Como a janela de contexto precisa caber inteira na grade, a
margem do sorteio subiu de 15 para 50 px, o que altera o conjunto sorteado —
determinístico, mesma seed.

### Consequência para a meta de §10

A acurácia **global** fica em 0,87–1,00 e cumpre a meta de 0,85 em todos os anos,
mas a comparação é fraca por construção: o estrato `nao_construido` ocupa
98–99,5 % da AOI. O número que discrimina é a acurácia do **usuário** da classe
`construido`, entre **0,27 e 0,63** — comissão alta e consistente. Publicado
como está. A acurácia do **produtor** não é utilizável com n = 24 por estrato:
um único ponto de referência do estrato `nao_construido` carrega ~4,1 % da área
da AOI no estimador.
