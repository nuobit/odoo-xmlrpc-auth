# odoo-xmlrpc-auth

A minimal CLI proxy for Odoo XML-RPC calls. Its only job is to **inject
credentials** so they never appear in command history or scripts.

## How it works

```
odoo-xmlrpc-auth --profile <name> '<json>'
         │                │          │
         │                │          └─ single JSON matching execute_kw signature
         │                └─ profile name → reads ~/.config/odoo-xmlrpc-auth/<name>.conf
         └─ authenticates via XML-RPC, executes, returns JSON
```

The JSON payload mirrors Odoo's `execute_kw` directly:

```json
{"model": "...", "method": "...", "args": [...], "kwargs": {...}}
```

The tool just adds `db`, `uid`, and `password` transparently.

## Examples

```bash
# Create a task
odoo-xmlrpc-auth --profile customer1 \
  '{"model":"project.task","method":"create","args":[{"name":"Bug: login broken","project_id":42}]}'

# Search with kwargs (fields, limit)
odoo-xmlrpc-auth --profile customer1 \
  '{"model":"project.task","method":"search_read","args":[[["project_id","=",5]]],"kwargs":{"fields":["name","stage_id"],"limit":10}}'

# Create an attachment
odoo-xmlrpc-auth --profile customer1 \
  '{"model":"ir.attachment","method":"create","args":[{"name":"screenshot.png","type":"binary","datas":"...","res_model":"project.task","res_id":123}]}'

# Read a record
odoo-xmlrpc-auth --profile customer1 \
  '{"model":"res.partner","method":"read","args":[[1]]}'
```

## Setup

### 1. Install

```bash
./install.sh
```

This copies `odoo-xmlrpc-auth` to `~/.local/bin/` (make sure it's in your PATH).

To update (downloads latest from GitHub):

```bash
./update.sh
```

To uninstall:

```bash
./uninstall.sh
```

### 2. Configure a profile

One file per Odoo instance, `chmod 600`:

```bash
mkdir -p ~/.config/odoo-xmlrpc-auth
chmod 700 ~/.config/odoo-xmlrpc-auth

cat > ~/.config/odoo-xmlrpc-auth/customer1.conf << 'CONF'
[odoo]
url=https://customer1.odoo.com
db=prod_db
user=user@example.com
password=your-api-key
CONF

chmod 600 ~/.config/odoo-xmlrpc-auth/customer1.conf
```

## Security model

| Data | Leaves your machine? |
|---|---|
| Odoo credentials | No — read by `odoo-xmlrpc-auth` locally from `~/.config/` |
| API call parameters | Yes — sent to Odoo via XML-RPC |
| API results | Yes — returned from Odoo via XML-RPC |

The wrapper is like `psql` reading `~/.pgpass` — credentials stay local,
only the queries go over the wire.

## Prerequisites

- **python3** (uses only stdlib: `xmlrpc.client`, `configparser`, `json`, `argparse`)
- No pip dependencies
