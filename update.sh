#!/usr/bin/env bash
set -euo pipefail

REPO="NuoBiT/odoo-xmlrpc-auth"
BIN_DIR="$HOME/.local/bin"
BIN_FILE="$BIN_DIR/odoo-xmlrpc-auth"

TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['tag_name'])")

if [[ -z "$TAG" ]]; then
    echo "Error: could not determine latest release tag" >&2
    exit 1
fi

URL="https://raw.githubusercontent.com/$REPO/$TAG/odoo-xmlrpc-auth.py"

echo "Downloading odoo-xmlrpc-auth $TAG..."
mkdir -p "$BIN_DIR"

tmp=$(mktemp "$BIN_DIR/odoo-xmlrpc-auth.XXXXXX")
cleanup() { rm -f "$tmp"; }
trap cleanup EXIT

curl -fsSL "$URL" -o "$tmp"
chmod 755 "$tmp"
mv "$tmp" "$BIN_FILE"
trap - EXIT

echo "Installed $TAG -> $BIN_FILE"
