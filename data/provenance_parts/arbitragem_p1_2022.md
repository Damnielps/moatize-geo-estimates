# Arbitragem — placebo espacial P1, quebra de 2022 (S_HARM_soma)

- **Data:** 2026-09-08
- **Papel:** segunda opinião obrigatória da Fase 3 (`docs/DESENHO_FASE3.md` §3.1) e arbitragem pedida em `ORCHESTRATION_LOG.md` 3-10.
- **Lido:** `docs/DESENHO_FASE3.md` (§0–§11), `pipeline/03_causal/placebos.py`, `data/processed/causal/{placebos,its_quebras,veredito_fase3,did_efeitos,did_sintetico_pesos,serie_luzes_anual}.csv`, `docs/ADR/0013`, `docs/ADR/0014`, log 3-09 e 3-10.
- **Nada foi alterado** em `pipeline/`, `data/processed/`, `docs/`.

## 0. O fato que muda a pergunta

A pergunta foi posta como "Tete cai enquanto as cinco capitais sobem". A série já publicada em
`serie_luzes_anual.csv` (coluna `soma_radiancia_adm2_int_recorte`, sensibilidade exigida por E6)
mostra que **a queda de 2022 não está na cidade de Tete**:

| 2021→2022, log-% | valor |
|---|---|
| Retângulo AOI (série primária) | **−6,2 %** |
| ADM2 `MZ0501` Cidade de Tete ∩ recorte (cobertura 0,845) | **+0,7 %** |
| Resto do retângulo (= Moatize + mina + corredor; 2 207 km² dos 2 494) | **−13,6 %** |

Dentro da cidade a luz não cai em 2022; cai **fora** dela, no lado do retângulo onde ficam
a mina e a vila de Moatize. A `max_radiancia` cai 63,7→49,9 no mesmo ano (E5) — o pixel mais
brilhante da AOI é, com toda a probabilidade, a planta de beneficiamento, não um bairro. E o
recorte de Tete tem 2 494 km² contra ~1 000–1 090 km² dos cinco controles: é o único dos seis
que **contém uma pegada industrial de escala** dentro da geometria.

A decomposição obrigatória de §2.3 ("dentro da pegada `industrial` / `urbano` fora da pegada /
resto — sem isso, uma queda de luz por fechamento de planta seria lida como queda de atividade
urbana") **não foi produzida**: não existe artefato em `data/processed/causal/` e nenhum script
de `pipeline/03_causal/` referencia a pegada. O desenho previu exatamente esta confusão e a
proibiu; a execução pulou a etapa.

Segundo fato: "Tete cai" é um ponto. 2023 +14,4 %, 2024 +3,6 %, 2025 +7,4 %; a soma de 2025
(9 366) está 19 % acima da de 2021. O que é verdade é **mais fraco**: Tete cresce 19 % (AOI) ou
37 % (ADM2) entre 2021 e 2025 enquanto os controles crescem 40–61 %, partindo de tendências
pré quase planas (b1 = −0,016 a +0,036) contra 0,072 de Tete. O b2 positivo dos cinco controles
é uma **aceleração comum a partir de 2021** (+13 %, +13 %, +3 %, +5 %, +13 % já em 2021), que o
modelo com t0 = 2022 aloca em nível + inclinação. Cinco capitais não tratadas acelerando em
uníssono de ~0 para ~13 %/ano em 2021–2025 é choque nacional ou produto (V2 estendido a 2025,
Dataverse V10) — em qualquer dos casos, não é contrafactual de Tete.

## 1. Veredito de P1 em 2022: manter, rever ou indeterminado?

**A favor de manter "FALHA".** A regra foi escrita antes do dado; o código (`placebos.py:185`)
implementa a disjunção b2-OU-b3 de forma literal; o ramo b3 dispara. Qualquer revisão depois
de ver que a regra reprova o resultado desejado é especificação procurada — o próprio
orquestrador o disse em 3-10. Manter o veredito custa nada e preserva o pré-registro.

**A favor de rever para "passa".** O ramo b3 não testou nada: 0,5 × |0,0083| = 0,0042 é
satisfeito por qualquer inclinação positiva. Um teste que não pode reprovar não é teste. E o
próprio desenho, em E8 (escrito **antes** de estimar placebos), declara que a inclinação pós
de 2022 é **"não estimável com 4 pontos"**. Aplicar a P1 um coeficiente que o pré-registro já
declarou não estimável não é seguir a regra; é violar E8. Só pelo ramo b2, zero controles
replicam e P1 "passa".

**A favor de "indeterminado".** Mesmo restringindo a b2, o que P1 compararia é a soma sobre
um retângulo com mina contra somas sobre retângulos sem mina. A divergência de sinal em b2
some quando a geometria é a cidade (ADM2: +0,7 %). P1 não está medindo "Tete vs. controles";
está medindo "mina de Moatize vs. cinco cidades". O teste está mal-posto em geometria, e um
teste mal-posto não passa nem falha.

**Conclusão: "não estimável — motivo", que é veredito admissível por §4.5, e não "FALHA" nem
"passa".** Motivo em uma linha: *o ramo b3 é vazio por E8 e o ramo b2 compara geometrias não
comparáveis sem a decomposição de §2.3*. "FALHA" está errado (o teste não reprovou Tete;
reprovou a si mesmo). "Passa" está errado (P1 pelo ramo b2 passaria por um artefato de
recorte). Registrar "FALHA" no artigo levaria o leitor a crer que os controles replicaram a
queda de Tete, o que é o oposto do que os dados mostram.

## 2. O defeito é genuíno? É do critério ou da aplicação?

**Genuíno, e é do critério — mas já estava coberto por uma cláusula pré-registrada que a
aplicação ignorou.** Duas camadas:

- **Critério:** "≥ 50 % da magnitude de Tete" é um teste de razão cujo denominador pode ser
  zero. Quando o coeficiente de referência é indistinguível de zero, a razão é indefinida e
  qualquer valor a satisfaz. É a mesma família de defeito de `docs/ADR/0014` (limiar relativo
  a denominador que colapsa), agora num critério estatístico. O desenho tinha à mão a
  ferramenta que faltou: em P2 (§4.2) o mesmo teste exige "IC95 que exclua zero" — em P1
  (§4.1) não. A assimetria é inexplicada e é a raiz.
- **Aplicação:** §4.1 diz "quebra do mesmo sinal e de magnitude ≥ 50 % da de Tete" sem nomear
  coeficiente. A leitura "b2 OU b3" é uma escolha de implementação (`placebos.py:185`),
  coerente com §4.2, mas **incompatível com E8**, que exclui b3 de 2022 como estimável. A
  aplicação usou um coeficiente que o próprio pré-registro tinha retirado da mesa.

Portanto: defeito de critério (denominador nulo) + erro de aplicação (ignorar E8). Nenhum dos
dois é "leitura do orquestrador": a leitura está correta.

## 3. Um conserto agora é lícito?

**Regra geral: não.** Corrigir o critério depois de ver que reprova o resultado atraente é a
definição de especificação procurada, independentemente de a correção ser "óbvia".

**Condições que tornariam uma emenda defensável, e se estão presentes:**

| Condição | Presente? |
|---|---|
| (a) A correção deriva de uma cláusula **já pré-registrada** antes do resultado, não de uma ideia nova | **Sim** para o ramo b3: E8 (2022: inclinação pós não estimável) antecede a estimação dos placebos. Aplicá-lo é cumprir o pré-registro, não emendá-lo |
| (b) A correção é **neutra quanto ao resultado**: aplicada a todas as quebras, não só à que incomoda | Aplicando "ramo só sobre coeficiente estimável e com IC que exclua zero" a 2005, 2011, 2016 e 2022: 2005 (1 replica) continua "passa"; 2011 (Tete b2 IC inclui zero; b3 exclui) — cai a 3 replicas em b3 (Chimoio, Lichinga, Xai-Xai), continua FALHA; 2016 continua FALHA (5 em b2); 2022 vai a 0 em b2. **Neutra em três de quatro; muda só a que degenera** |
| (c) A emenda é **datada, declara que o autor viu o dado**, e mantém o veredito original legível ao lado | Exigido por §10; fácil de cumprir |
| (d) A emenda **não produz resultado causal publicável** que antes não existia | **Sim**: F3 e F4 já disparam para B_luz_HARM 2022 (RMSPE pré > ½ DP; sintético = Inhambane com peso 1,0); DiD −0,12 com IC [−0,276; +0,035]; p de permutação 0,333. O contrafactual de 2022 está "NÃO SUSTENTADO" por critérios que não dependem de P1. Um P1 "passa" não reabilita nada |

**Veredito sobre licitude:** aplicar E8 ao ramo b3 é lícito porque não é emenda — é execução
de cláusula anterior. **Acrescentar** "IC que exclua zero" a P1 (espelhando P2) é emenda
genuína: lícita só como **emenda datada, declarada pós-dado, aplicada às quatro quebras, com
os dois vereditos (original e emendado) publicados lado a lado** e com a demonstração (b)
de que só altera a quebra degenerada. Recomendo fazê-la assim, e nunca substituindo o
veredito original no CSV: coluna nova `veredito_emenda2`, não sobrescrita.

O que **não** é lícito: reformular P1 para "b2 apenas" porque em 2022 b2 dá o resultado
atraente. Isso escolhe o coeficiente pelo resultado.

## 4. A divergência de sinal em 2022 é substantiva ou artefato?

Argumento por explicação alternativa, em ordem de força:

1. **Geometria (E6) — explica a queda de Tete quase por inteiro.** A queda está fora do ADM2
   (−13,6 %) e ausente dentro (+0,7 %). Sem a decomposição de §2.3, o que se pode dizer é que
   a luz da parte não-urbana do retângulo (mina, Moatize, corredor) caiu em 2022. Isso é
   coerente com a transição Vale→Vulcan (venda concluída abr/2022) e pode ser resultado — mas
   é resultado **sobre a pegada minerária**, não sobre "Tete". Como afirmação sobre a cidade,
   é **artefato de recorte**.
2. **Aceleração comum dos controles a partir de 2021** — explica o b2 positivo deles. Cinco
   capitais a centenas de km acelerando em uníssono de ~0 para 10–25 %/ano é choque nacional
   (expansão da rede EDM, pós-Covid) ou comportamento do produto V2 nos anos de extensão
   (2023–2025 são anos recentes do V10). Tete também acelera em 2023 (+14,4 %). A "divergência
   de sinal" é em boa parte "Tete já crescia a 7 %/ano e não acelerou; os outros partiram do
   zero e aceleraram".
3. **Costura DMSP→VIIRS (E4)** — fora da janela; **não** explica 2022. Concordo com E5.
4. **Queda do máximo (E5)** — o argumento "soma sobe com máximo caindo = dispersão" é correto
   para 2023–2025, mas em **2022** a soma **e** o máximo caem juntos (−6,2 % e 63,7→49,9). Em
   2022 especificamente, E5 não separa produto de economia; separa só a partir de 2023. E o
   pixel máximo estar fora do ADM2 reforça que é a planta.
5. **P2 (2019)** passou por 2 pontos percentuais: b2 do placebo = −0,087, 48 % do real, com IC
   que exclui zero e b3 = −0,054 também significativo. O modelo segmentado encontra "quebra"
   negativa em 2019 quase tão grande quanto a de 2022. A datação é frágil.
6. **p mínimo 1/6.** Rank 2 de 6, p = 0,333. Nada aqui atinge significância por permutação, e
   HAC com T = 13 sub-cobre (§2.2.4).

**Conclusão:** como afirmação "Tete diverge dos controles em 2022", **não há resultado
defensável**. O que sobrevive é descritivo e mais estreito: (i) a luz na parte do retângulo
fora da cidade de Tete caiu ~14 % em 2022 e não recuperou o ritmo anterior (2025 ≈ 2023);
(ii) a luz da cidade (ADM2) não caiu em 2022 e cresceu 37 % em 2021–2025, abaixo dos controles
(40–61 %). (i) só vira afirmação sobre a mina depois da decomposição de §2.3. (ii) é comparação
bilateral sem contrafactual sustentado (F3, F4).

## 5. ADR?

**Sim — um ADR, decidindo quatro coisas:**

1. **Regra geral de critérios relativos:** nenhum teste "≥ x % da magnitude de referência" é
   aplicado a coeficiente cujo IC95 inclua zero ou que o desenho declare não estimável; nesse
   caso o ramo é "vazio" e o veredito, se todos os ramos forem vazios, é "não estimável".
   Aplicado retroativamente a P1 e P2 nas quatro quebras, com os dois vereditos publicados.
2. **P1-2022: veredito reclassificado de "FALHA" para "não estimável — ramo b3 vazio (E8);
   ramo b2 sem decomposição de §2.3"**, com o "FALHA" original mantido em coluna própria.
3. **A decomposição de luz de §2.3 é pré-requisito** de qualquer frase sobre 2022, e sua
   ausência é registrada como etapa não executada (não "não estimável": a pegada existe em
   ADR 0011/0014). Até ela existir, a quebra de 2022 é publicada só com a série ADM2 ao lado.
4. **Sétima ocorrência do padrão "denominador que colapsa"** (ADR 0014 lista seis), primeira
   num critério estatístico — registrada como lição, com a assimetria P1/P2 como causa.

O ADR **não** decide que 2022 é resultado. Decide que o teste estava mal-posto e que a
afirmação sobre a cidade não sobrevive à sensibilidade de geometria já publicada.

## Custo

Fase 3, camada `03_causal`: (a) coluna `veredito_emenda2` em `placebos.py` (< 1 h);
(b) decomposição de §2.3 — soma de radiância por máscara `industrial`/`urbano`/resto, 13 anos
× 3 recortes, com a pegada de ADR 0011/0014 reamostrada a ~500 m (1 sessão); (c) ADR (< 1 h).
Nada volta à Fase 1 ou 2.
