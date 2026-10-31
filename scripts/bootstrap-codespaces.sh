#!/usr/bin/env bash
set -Eeuo pipefail

# Instalação automatizada e idempotente do laboratório, sem acesso aos outros projetos.
# Fonte da ferramenta: https://github.com/Alishahryar1/free-claude-code
# Fixamos uma versão para evitar executar automaticamente código de uma revisão futura.
FCC_VERSION="6.18.5"
CLAUDE_VERSION="2.1.308"
LOCAL_BIN="$HOME/.local/bin"
VENV="$HOME/.local/share/fcc-bootstrap-venv"
mkdir -p "$LOCAL_BIN" "$HOME/.local/share"

echo "[1/4] Preparando gerenciador Python isolado..."
if [ ! -x "$VENV/bin/uv" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/python" -m pip install --disable-pip-version-check --no-input 'uv>=0.8,<1'
fi
export PATH="$LOCAL_BIN:$VENV/bin:$PATH"
"$VENV/bin/uv" python install 3.14

echo "[2/4] Instalando Free Claude Code v${FCC_VERSION}..."
"$VENV/bin/uv" tool install --python 3.14 "free-claude-code==${FCC_VERSION}"
command -v fcc-server >/dev/null || { echo "Erro: fcc-server nao encontrado."; exit 1; }
fcc-server --version

echo "[3/4] Instalando cliente Claude Code v${CLAUDE_VERSION}..."
if ! command -v npm >/dev/null 2>&1; then
  echo "Erro: Node.js/npm ausentes no Codespaces."
  exit 1
fi
npm_config_prefix="$HOME/.local" npm install -g --no-audit --no-fund "@anthropic-ai/claude-code@${CLAUDE_VERSION}"
command -v claude >/dev/null || { echo "Erro: comando claude nao encontrado."; exit 1; }
claude --version

echo "[4/4] Configurando PATH para novas sessoes..."
if ! grep -Fq 'FCC_LAB_PATH' "$HOME/.bashrc"; then
  printf '\n# FCC_LAB_PATH - Ferramentas locais do laboratorio\nexport PATH="$HOME/.local/bin:$HOME/.local/share/fcc-bootstrap-venv/bin:$PATH"\n' >> "$HOME/.bashrc"
fi
echo "Instalacao de ferramentas concluida."
echo "O servidor NAO foi iniciado e nenhuma chave foi configurada."
echo "Para usar o painel, execute fcc-server em uma sessao privada."
