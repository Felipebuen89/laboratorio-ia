#!/usr/bin/env bash
set -euo pipefail

# Revisão fixada em um commit específico do projeto de origem.
SOURCE_COMMIT="653a3444d43c0489c26d1b3a2e2a336b001e20ff"
SOURCE_URL="https://raw.githubusercontent.com/Alishahryar1/free-claude-code/${SOURCE_COMMIT}/scripts/install.sh"

temp_file="$(mktemp)"
trap 'rm -f "$temp_file"' EXIT

echo "Baixando instalador fixado em ${SOURCE_COMMIT} ..."
curl --proto '=https' --tlsv1.2 -fsSL --retry 2 --max-time 60 "$SOURCE_URL" -o "$temp_file"
test -s "$temp_file"
sh -n "$temp_file"

echo
echo "Verificacao de sintaxe: OK"
sha256sum "$temp_file"
echo
echo "O programa ainda NAO foi instalado."
echo "O instalador original e de terceiros e pode baixar outros componentes."
echo "Se prosseguir, selecione apenas os agentes que deseja usar quando solicitado."
read -r -p "Continuar a instalacao no Codespaces? [s/N] " resposta
case "$resposta" in
  s|S|sim|SIM|Sim) sh "$temp_file" ;;
  *) echo "Instalacao cancelada. Nenhuma etapa do instalador foi executada." ;;
esac
