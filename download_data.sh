#!/usr/bin/env bash
# Baixa os dados públicos de CEP, cidades, estados e países
# Uso: ./download_data.sh [diretório_destino]
set -euo pipefail

DATA_DIR="${1:-./data}"
mkdir -p "$DATA_DIR"
BASE_URL="https://raw.githubusercontent.com/vmsouza/ceps-brasil-data/main"

echo "Baixando dados públicos para $DATA_DIR..."

for file in paises.json estados.json cidades.json tipos_logradouros.ndjson correios_ceps.ndjson.gz; do
    echo "  $file..."
    curl -sL "$BASE_URL/$file" -o "$DATA_DIR/$file"
done

echo "Pronto! Dados salvos em $DATA_DIR"
