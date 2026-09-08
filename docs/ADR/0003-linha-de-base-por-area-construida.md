# ADR 0003 — Linha de base 1997–2005 reconstruída por área construída, não por população

- **Data:** 2026-09-07
- **Fase:** 0' (Reconhecimento)
- **Decidido por:** usuário, sobre recomendação do orquestrador
- **Estado:** aceito

## Contexto

§2 define **1997–2005 como a fase de linha de base contrafactual**, anterior à concessão
da Vale (2004). §5.4 exige um período pré-tratamento para testar tendência paralela antes
de qualquer diferença-em-diferenças ou controle sintético. E **H1** afirma que o
crescimento populacional de Tete acelera de ~4 %/ano (1997–2007) para ~7 %/ano (2007–2017).

Os três dependem do **Censo de 1997 (II RGPH)**.

Na Fase 0' o Censo 1997 foi procurado exaustivamente e **não foi localizado em fonte
primária acessível**:

| Via | Resultado |
|---|---|
| `ine.gov.mz` (todas as variantes) | **000** — fora do ar, não intermitente |
| Catálogo `mozdata.ine.gov.mz` | responde 200, mas **não lista o Censo 1997**; só 2007 e 2017 |
| Internet Archive, sete padrões de URL | confirma que a **brochura provincial de Tete do II RGPH existiu** (pasta `05`), mas **as páginas com os números nunca foram arquivadas** |

Os censos de **2007 e 2017 foram recuperados e conferidos** (Cidade de Tete 155.870 e
307.338; Distrito de Moatize 215.092 e 260.843). Só a ponta de 1997 falta.

Some-se a isso o veredito de `data/DATA_AUDIT.md`: sem texto de licença localizável, os
documentos do INE são **nível C** por §4.0 regra 1 — o que atinge as três âncoras
censitárias, não apenas a de 1997.

## Decisão

A linha de base 1997–2005 passa a ser reconstruída por **área construída**, não por
população recenseada. A fonte é o **WSF Evolution (DLR)**: máscara anual de assentamento,
30 m, **1985–2015**, nível A.

**H1 é reformulada em termos de área**, e não de habitantes. A formulação original
— aceleração de ~4 %/ano para ~7 %/ano na população — deixa de ser testável com fonte de
nível A e não pode ser mantida como está.

Três consequências que a nova formulação precisa carregar explicitamente:

1. **Área construída não é população.** A razão entre as duas (intensidade de uso) varia
   com renda, tipologia e densidade domiciliar, e num boom minerário varia justamente por
   causa do tratamento. Qualquer leitura de "crescimento" passa a ser sobre a mancha, e a
   passagem para habitantes exige a dasimetria de §5.3 — que herda a incerteza.
2. **A série anual é mais densa que a decenal.** Onde havia três pontos (1997, 2007, 2017),
   passa a haver dezenove observações anuais entre 1997 e 2015, o que **fortalece** o teste
   de tendência paralela de §5.4 em vez de enfraquecê-lo.
3. **O WSF Evolution termina em 2015.** A ponta 2015–2025 fica com GHSL, WSF 2019 e a
   classificação própria do §5.1 — protocolos diferentes, cuja compatibilidade tem de ser
   demonstrada, não presumida.

## Alternativas rejeitadas

**Recuar a linha de base para 2007.** Rejeitada porque 2007 já é **posterior** à concessão
da Vale (licitação 2004, licença 2006) e ao início das obras (~2007). A fase "pré-projetos"
de §2 desapareceria, e com ela o período pré-tratamento que §5.4 exige: sem pré-tratamento
não há teste de tendência paralela, e o contrafactual de §5.5 fica indefensável. Seria
trocar uma hipótese não testável por um desenho causal não defensável.

**Aceitar 101.984 e 109.103 como valores secundários marcados.** Rejeitada porque esses
números só existem em agregadores (citypopulation.de, Wikipedia). §4.0 regra 4 é explícita:
agregador serve para localizar, nunca para citar. E §10 exige que todo número publicado
derive de fonte de nível A. Admitir o valor "só para ordem de grandeza" abriria exceção
justamente no ponto que ancora a hipótese central — o pior lugar possível para uma exceção.

## Consequência

- **H1 tem de ser reescrita** antes da Fase 3, em termos de área construída. A redação
  atual em `CLAUDE.md` §1 e no prompt-mestre está desatualizada neste ponto.
- **A pergunta 1 de §1** ("ritmo e forma de crescimento antes da mineração") continua
  respondível, e com resolução temporal melhor que a original.
- **A pergunta 6** ("bust e transição, 2015–2025") continua sem âncora demográfica: não há
  censo depois de 2017 e o de 2027 ainda não existe.
- `pipeline/00_fetch/fetch_wsf_evolution.py` deixa de ser opcional e passa a ser
  **caminho crítico** da Fase 1. Hoje ele é um script de deferimento ao GEE/STAC, sem
  download próprio — precisa virar obtenção de verdade.
- Toda série derivada do WSF Evolution recebe selo **`observado`** (é máscara classificada,
  não modelo), e a conversão para população recebe selo **`modelado`**.
