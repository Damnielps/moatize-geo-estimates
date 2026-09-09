## `paper/FATOS_VERIFICADOS.md` — folha de fatos do artigo

- **Gerado por:** `pipeline/04_figures/fatos_verificados.py`, alvo `figures` do Makefile.
- **Selo:** derivado — nenhum valor é observado aqui; todos são recalculados de
  `data/processed/` a cada execução.
- **Nível da fonte:** A (todos os insumos são `data/processed/`, que só contém nível A).
- **Não editar à mão.** O arquivo é sobrescrito por `make figures`.

**Insumos:** `acuracia_por_ano.csv` · `causal/estabilidade_temporal_camadas.csv` ·
`causal/decomposicao_luz_por_camada.csv` · `causal/its_quebras.csv` ·
`causal/veredito_fase3.csv` · `causal/placebos.csv` · `causal/serie_luzes_anual.csv`.

**Por que existe (ORCHESTRATION_LOG.md 4-03 a 4-11).** A Fase 4 reprovou seis vezes por
**afirmação relacional**: número certo, qualificador errado — mediana citada como máximo,
acurácia citada como comissão, valor anterior à reexecução do `docs/ADR/0014` citado como
corrente. Todas vieram do orquestrador citando de memória. O artigo da Fase 5 é a maior
superfície de prosa do projeto e escreveria sobre os mesmos números.

Cada número aqui vem com **a estatística que ele é** (faixa entre anos, mediana, máximo,
ano único) e uma linha **"Como escrever"** que declara o que pode e o que não pode ser
afirmado sobre ele — por exemplo, que "até N" só admite o máximo medido, jamais a mediana;
que um p = 0,000 descreve a série de Tete mas não mede efeito do carvão; e que a queda de
luz de 2022 está fora da cidade e **não** pode ser atribuída à mina (`docs/ADR/0015`).

**Erro relacional encontrado dentro da própria folha, na sexta passagem do portão:** a
versão inicial dizia que os quatro painéis caíam "porque o placebo espacial mostra a mesma
quebra em capitais sem carvão" — verdadeiro em 2011 e 2016, **falso** em 2005 e 2022, onde
P1 é *não estimável*. O motivo passou a ser lido do CSV por quebra, em vez de generalizado.
