#!/bin/bash
# Genera informes/<region>.pdf (25) y informes/peru.pdf imprimiendo las carátulas en modo informe (?pdf=1) con Chrome headless.
# Uso: python3 -m http.server 8765 &  ;  bash scripts/build_pdfs.sh
set -e
cd "$(dirname "$0")/.."
CH="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
BASE="${BASE:-http://localhost:8765}"
mkdir -p informes
pdf(){ timeout 90 "$CH" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=12000 --window-size=1200,1600 --print-to-pdf="informes/$1.pdf" "$BASE/$2?pdf=1" 2>/dev/null || echo "falló $1"; }
pdf peru region/
for d in region/*/; do s=$(basename "$d"); [ -f "region/$s/index.html" ] && pdf "$s" "region/$s/"; done
ls -la informes | tail -n +2 | wc -l
