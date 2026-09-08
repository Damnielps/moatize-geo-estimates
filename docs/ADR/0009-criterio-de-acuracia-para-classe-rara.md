# ADR 0009 — Acurácia global sai do critério de qualidade; entram acurácia do usuário e do produtor da classe rara

- **Data:** 2026-09-07
- **Fase:** 1 (Pipeline de imagem)
- **Decidido por:** usuário, sobre recomendação do orquestrador
- **Estado:** aceito

## Contexto

§10 do prompt-mestre exige "acurácia global **≥ 85 %** por ano, ou justificativa explícita".
A validação da Fase 1 mostrou que esse critério **não discrimina** neste problema.

| ano | acurácia global | IC95 | kappa | acurácia do usuário, `construido` | peso do estrato construído |
|---|---|---|---|---|---|
| 2000 | 0,997 | ±0,001 | 0,68 | 0,52 | 0,56 % |
| 2005 | 0,997 | ±0,002 | 0,74 | 0,58 | 0,83 % |
| 2010 | 0,991 | ±0,002 | 0,43 | **0,27** | 1,18 % |
| 2015 | 0,950 | ±0,084 | 0,23 | 0,54 | 1,55 % |
| 2020 | 0,869 | ±0,133 | **0,09** | 0,52 | 1,65 % |
| 2025 | 0,993 | ±0,004 | 0,77 | 0,63 | 1,93 % |

**Os seis anos passam no critério de §10.** E, no entanto, entre **37 % e 73 %** do que o
mapa chama de construído não é construído.

A causa é aritmética, não acidental: a classe de interesse ocupa **0,56 % a 1,93 %** da AOI.
Um classificador que marcasse *tudo* como não-construído — isto é, que falhasse
completamente no objeto do estudo — obteria acurácia global entre **98,1 % e 99,4 %**, bem
acima do limiar. **O critério é satisfeito por construção e não carrega informação.**

O kappa detecta o problema (0,09 em 2020), mas §10 não o exige.

## Decisão

O critério de acurácia de §10 passa a ser, **por ano e por classe de interesse**:

1. **Acurácia do usuário (1 − comissão)** da classe `construido`, e das três camadas quando
   avaliadas separadamente, **com intervalo de confiança de 95 %**.
2. **Acurácia do produtor (1 − omissão)** das mesmas classes, com IC95 — **ou a declaração
   explícita de que o tamanho amostral não a torna estimável**, com a alavanca de área de um
   ponto do estrato majoritário informada. Não se reporta produtor instável como se fosse
   estimativa.
3. **Kappa**, que já constava, agora com peso de critério e não de acompanhamento.
4. **Acurácia global permanece reportada**, com IC95, mas **deixa de ser critério de
   aprovação**. Vira contexto.
5. **A prevalência de cada classe é publicada junto** de qualquer métrica de acurácia. Sem
   ela, nenhum dos números acima é interpretável.

**Não se fixa um limiar numérico para a acurácia do usuário.** Um limiar arbitrário sobre a
classe rara reproduziria o vício que este ADR corrige, só que na direção oposta — e a
literatura de sensoriamento remoto não sustenta um valor único para construído esparso a
30 m em ambiente semiárido. O que se exige é que o número seja **medido, publicado com IC,
e que toda conclusão derivada declare a incerteza que ele impõe**.

## Alternativa rejeitada

**Manter §10 e publicar a acurácia do usuário como ressalva.** Rejeitada porque deixaria no
repositório um critério que **aprova qualquer coisa** numa AOI onde a classe de interesse é
1 % — inclusive um mapa vazio. O critério não estava sendo mal aplicado; ele estava errado.
Corrigir só o relato preservaria a armadilha para a próxima fase e para quem reproduzisse o
estudo.

## Consequência

- **§10 do `CLAUDE.md` e do prompt-mestre precisam ser reescritos** neste ponto.
- **A Fase 1 não passa a ser reprovada retroativamente.** Ela mede e publica o que o novo
  critério exige; o que muda é que o número decisivo passa a ser 0,27–0,63, e não 0,87–0,997.
- **O papel da classificação fica restrito**, conforme decidido em paralelo: ela serve para
  **separar as três camadas** (urbano, reassentamento, industrial-minerário), que é o que só
  ela faz; a **série de área construída** é a do WSF Evolution, por `docs/ADR/0008`.
- **Toda métrica de forma urbana de §5.2** carrega a comissão medida como **incerteza
  declarada**, não como ruído ignorado. Isso vale para fragmentação, rosa de expansão e
  tipologia infill/borda/leapfrog.
- O `qa-validador` passa a julgar por este critério, não pelo antigo.

## Nota sobre o que tornou o problema visível

A acurácia do usuário só apareceu porque a validação foi feita com **amostragem
estratificada pelo mapa** e estimador de Olofsson et al. (2014), que exige reportar as
métricas por classe. Uma validação por amostragem simples teria produzido a acurácia global
alta, satisfeito §10, e escondido a comissão — com muito menos trabalho.
