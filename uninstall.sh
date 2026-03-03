#!/usr/bin/env bash
set -euo pipefail

BIN_FILE="$HOME/.local/bin/odoo-xmlrpc-auth"

if [[ -f "$BIN_FILE" ]]; then
    echo "Removing $BIN_FILE"
    rm "$BIN_FILE"
else
    echo "odoo-xmlrpc-auth not found (already removed?): $BIN_FILE"
fi

echo "Done."
