# ADR 0015 — Ramo de teste relativo com referência nula, e a decomposição que 2022 exige

- **Data:** 2026-09-08
- **Fase:** 3
- **Decidido por:** orquestrador, sobre parecer do `revisor-adversarial`
  (`data/provenance_parts/arbitragem_p1_2022.md`), pedido em `ORCHESTRATION_LOG.md` 3-10
- **Estado:** aceito

## Contexto

O placebo espacial P1 reprovou nas quatro quebras. Em 2016 a reprovação é sólida e é
**achado**: Tete cai −0,152 em nível e quatro das cinco capitais sem carvão caem **mais**
(−0,183 a −0,396). Uma quebra de "bust do carvão" que aparece com mais força onde não há
carvão não é do carvão.

Em 2022 o orquestrador contestou o veredito. Tete tem b2 = **−0,181** e os cinco controles
têm b2 **positivo** (+0,022 a +0,277): divergência de **sinal**, o único ponto do estudo em
que Tete se separa de todos os controles. O P1 reprovava pelo ramo **b3**, onde Tete vale
**+0,0083 com IC95 [−0,0159; +0,0324] — que inclui zero**. O teste "≥50 % da magnitude de
Tete" vira "≥0,0042", que qualquer número satisfaz.

O orquestrador **não reverteu o veredito** e escalou, declarando ao revisor que tinha
interesse na resposta, para que isso fosse tratado como viés a controlar.

## O que o revisor achou, e que ninguém tinha perguntado

**A queda de 2022 não está na cidade.** A decomposição pela interseção com o ADM2, já
presente em `data/processed/causal/serie_luzes_anual.csv` por força da Emenda E6, foi
conferida pelo orquestrador em disco:

| janela | retângulo inteiro | Cidade de Tete | resto (Moatize + mina) |
|---|---|---|---|
| 2021 → 2022 | −6,0 % | **+0,7 %** | **−12,7 %** |
| 2020 → 2022 | −5,3 % | −1,2 % | −9,6 % |
| 2021 → 2025 | +21,2 % | **+45,0 %** | **−2,5 %** |

O "Tete cai enquanto os controles sobem" é **artefato de recorte**: o retângulo de Tete
contém a mina e a vila de Moatize; nenhum retângulo de controle contém mina. A cidade de
Tete não cai em 2022 — ela **cresce 45 % entre 2021 e 2025**, enquanto o resto do retângulo
recua 2,5 %.

## Decisão

1. **Regra geral — ramo de teste relativo com referência nula é ramo vazio.** Num critério
   que compara magnitude contra um coeficiente de referência, o ramo é **inaplicável**
   quando esse coeficiente tem IC95 que inclui zero ou foi declarado não estimável. Não é
   "passa" nem "falha": é **não estimável, com motivo**. Vale para P1, P2 e qualquer regra
   futura da mesma forma. A assimetria de origem — P2 exigia "IC exclui zero" e P1 não —
   era inexplicada e fica eliminada.

2. **P1 em 2022 é reclassificado como "não estimável — motivo".** O ramo b3 é vazio pela
   regra 1 e pela Emenda E8, que já havia declarado a inclinação pós-2022 não estimável
   **antes** de os placebos rodarem — aplicar E8 aqui é execução de cláusula anterior, não
   emenda nova. O ramo b2 compara geometrias não comparáveis (regra 4). O veredito
   **"FALHA" original é preservado em coluna própria**, lado a lado, nunca sobrescrito.

3. **Isto não reabilita nada, e é a condição que torna a mudança lícita.** O contrafactual
   de 2022 continua derrubado por **F3** e por **F4** — o sintético é Inhambane com peso
   1,000, e o DiD dá −0,12 com IC95 [−0,28; +0,03] e p = 0,333. Corrigir uma regra que não
   muda nenhuma conclusão não é procurar especificação que passe.

4. **Nenhuma frase sobre a mina em 2022 antes da decomposição de §2.3.** A separação
   industrial / urbano / resto que o desenho exige nunca foi produzida. Sem ela, o que
   existe é descritivo e assim tem de ser publicado: a luz fora da cidade cai ~13 % em 2022
   e estagna até 2025; a luz da cidade cresce 45 % no mesmo período, abaixo dos controles
   (40–61 %). **Etapa registrada como não executada**, não como pendência menor.

5. **Sétima ocorrência do padrão de `docs/ADR/0014`** — e a primeira num critério
   estatístico, não num limiar de processamento. As seis anteriores: máscara de
   denominador, corte de treino de vegetação, limiar de construído, timeout de rede,
   tolerância de bbox e escopo de contrato. A forma da correção é sempre a mesma: trocar a
   constante ou a razão frágil pela **unidade natural da grandeza** — aqui, a
   significância do coeficiente de referência.

## O que isto custa ao estudo

**O único ponto em que Tete se separava de todos os controles não sobrevive.** A resposta à
pergunta 6 de §1 — se a cidade "ficou maior que a economia que a criou" — deixa de ter
suporte causal e passa a ter suporte **descritivo e interno à AOI**: a luz da mina e de
Moatize recua enquanto a da cidade acelera. É uma afirmação mais fraca do que a que eu
esperava fazer, e é a que o dado sustenta.

## Lição registrada

O defeito foi achado porque o veredito **contrariava** o interesse do orquestrador e ele
escalou em vez de reescrever a regra. Mas o que o revisor trouxe não foi a resposta à
pergunta feita — foi o fato de que a pergunta estava mal posta, porque ninguém tinha olhado
**onde**, dentro do retângulo, a luz caía. A decomposição estava no CSV desde a Emenda E6.
Ninguém a leu antes de discutir o veredito, o orquestrador inclusive.
