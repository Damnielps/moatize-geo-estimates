# Imagem que executa o pipeline completo (§11.1, §11.2.5).
# Ver docs/ADR/0002 para a escolha de uv em vez de conda.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
      make git ca-certificates curl jq \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.1 /uv /usr/local/bin/uv

WORKDIR /work

# Camada de dependências: só invalida quando o lock muda.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY . .

CMD ["make", "all"]
