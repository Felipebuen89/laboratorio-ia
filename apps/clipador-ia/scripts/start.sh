#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .runtime
if [[ -f .runtime/server.pid ]] && kill -0 "$(cat .runtime/server.pid)" 2>/dev/null; then
  echo "Clipador IA já está em execução."
  exit 0
fi
CLIPADOR_HOST=0.0.0.0 nohup .venv/bin/python ui.py > .runtime/server.log 2>&1 < /dev/null &
echo $! > .runtime/server.pid
echo "Clipador IA iniciando na porta privada 7860 (ver aba Ports do Codespaces)."
