"""§5.6.4 — logit espacial de conversao cropland->construido.

NAO EXECUTADO, e isto e o resultado, nao uma omissao. A condicao pre-registrada
(§7 do desenho: opcao C de docs/ADR/0013 executada e aprovada) NAO foi satisfeita.
O script existe para que a recusa seja reproduzivel e datada.
Saida: data/processed/causal/logit_conversao_status.csv
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

SAIDA = Path(__file__).resolve().parents[2] / "data" / "processed" / "causal"


def main() -> None:
    linhas = [{
        "item": "logit espacial de conversao cropland->construido (§5.6.4)",
        "estado": "NAO DETERMINAVEL COM ESTA SERIE",
        "bloqueio_1": ("churn de 31-54% na identidade pixel a pixel de `construido` entre "
                       "anos-ancora consecutivos (ADR 0013 §2/§3). O desfecho do logit e "
                       "literalmente 'este pixel mudou'."),
        "bloqueio_2": ("`cultivo_sequeiro` nao e defensavel como cropland (ADR 0012, "
                       "confirmado por ADR 0014: kappa -0,065, Jaccard 0,001-0,002 contra "
                       "GLAD). Sem classe de origem, 'cropland->construido' nao e definivel."),
        "condicao_para_rodar": ("opcao C de docs/ADR/0013 (limiar relativo propagado MAIS "
                                "uma abordagem de cultivo que nao seja a fenologia bianual "
                                "reprovada), executada e aprovada. Decisao do orquestrador."),
        "autocorrelacao_espacial": ("o tratamento estava especificado (erros agrupados em "
                                    "blocos >= 2x o alcance do variograma do residuo, I de "
                                    "Moran sobre os residuos, especificacao autologistica ao "
                                    "lado). NADA DISSO FOI EXECUTADO — nao ha residuo sobre "
                                    "que medir Moran porque nao ha modelo."),
        "o_que_seria_produzido_se_rodasse_assim_mesmo": (
            "coeficientes significativos e sem conteudo: com 31-54% de churn no desfecho, "
            "qualquer covariavel com estrutura espacial ganharia significancia."),
        "h5": "bloqueada pelos mesmos dois pre-requisitos; permanece rebaixada",
        "seed_reservada": 24680,
    }]
    pd.DataFrame(linhas).to_csv(SAIDA / "logit_conversao_status.csv", index=False)
    print("§5.6.4: nao determinavel com esta serie (bloqueio pre-registrado, §7 do desenho).")


if __name__ == "__main__":
    main()
