#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="$HOME/.local/bin"

echo "Installing odoo-xmlrpc-auth -> $BIN_DIR/"
mkdir -p "$BIN_DIR"
install -m 755 "$SCRIPT_DIR/odoo-xmlrpc-auth.py" "$BIN_DIR/odoo-xmlrpc-auth"

echo "Done. Make sure $BIN_DIR is in your PATH."
