#!/usr/bin/env bash
# log_cost.sh — hook SubagentStop.
# Lê o JSON do hook em stdin e faz append de uma linha em cost_ledger.csv.
# Se o payload não trouxer contagem de tokens, registra turnos e o tamanho do
# resumo devolvido como proxy (§0-A.5 do prompt-mestre).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LEDGER="$REPO_ROOT/cost_ledger.csv"

payload="$(cat)"

# O payload real do SubagentStop nesta versão do Claude Code não traz `model` nem
# contagem de tokens: as linhas gravadas na Fase 0' saíram todas com `unknown` e
# campos vazios. Sem conhecer o esquema não dá para corrigir os seletores `jq`,
# então guardamos o payload bruto (um JSON por linha) para inspeção. É a única
# via de instrumentar custo e de fazer a conferência de modelo exigida por §0-B.
DEBUG_JSONL="$REPO_ROOT/data/interim/subagent_stop_payloads.jsonl"
mkdir -p "$(dirname "$DEBUG_JSONL")"
printf '%s\n' "$payload" >> "$DEBUG_JSONL"

if [ ! -f "$LEDGER" ]; then
  echo "timestamp,agent_type,model,turns,input_tokens,output_tokens,summary_chars,proxy" > "$LEDGER"
fi

read_field() {
  printf '%s' "$payload" | jq -r "$1 // empty" 2>/dev/null || true
}

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
agent="$(read_field '.agent_type // .subagent_type // .agent.name')"
model="$(read_field '.model // .agent.model // .usage.model')"
turns="$(read_field '.num_turns // .turns // .agent.turns')"
in_tok="$(read_field '.usage.input_tokens // .total_usage.input_tokens')"
out_tok="$(read_field '.usage.output_tokens // .total_usage.output_tokens')"
summary="$(read_field '.result // .summary // .last_message')"

sum_chars="${#summary}"
proxy="false"
if [ -z "$in_tok" ] && [ -z "$out_tok" ]; then
  proxy="true"
fi

printf '%s,%s,%s,%s,%s,%s,%s,%s\n' \
  "$ts" "${agent:-unknown}" "${model:-unknown}" "${turns:-}" \
  "${in_tok:-}" "${out_tok:-}" "$sum_chars" "$proxy" >> "$LEDGER"

exit 0
