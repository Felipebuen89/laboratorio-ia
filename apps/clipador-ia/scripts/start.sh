#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .runtime

# Keep the Codespaces port private. This process only starts a local service.
check_health() {
  .venv/bin/python - <<'PY'
import sys
import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:7860/", timeout=3) as response:
        if response.status != 200:
            sys.exit(1)
except Exception:
    sys.exit(1)
PY
}

if [[ -f .runtime/server.pid ]] && kill -0 "$(cat .runtime/server.pid)" 2>/dev/null; then
  if check_health; then
    echo "Clipador IA já está funcionando na porta 7860."
    exit 0
  fi
  echo "Processo antigo encontrado, mas sem resposta HTTP; tentando recuperar."
  kill "$(cat .runtime/server.pid)" 2>/dev/null || true
fi

CLIPADOR_HOST=0.0.0.0 nohup .venv/bin/python ui.py > .runtime/server.log 2>&1 < /dev/null &
pid=$!
echo "$pid" > .runtime/server.pid
for attempt in $(seq 1 90); do
  if check_health; then
    echo "Clipador IA confirmado: http://127.0.0.1:7860/ (abrir porta PRIVADA no Codespaces)."
    exit 0
  fi
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "O servidor encerrou durante a inicialização. Últimos logs:"
    tail -60 .runtime/server.log || true
    exit 1
  fi
  sleep 1
done
echo "O servidor não respondeu no limite de inicialização. Últimos logs:"
tail -60 .runtime/server.log || true
exit 1
