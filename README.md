# odoo-xmlrpc-auth

A minimal CLI proxy and Python library for Odoo XML-RPC calls. Its only job
is to **inject credentials** so they never appear in command history or scripts.

## Install

```bash
pip install git+https://github.com/NuoBiT/odoo-xmlrpc-auth.git
```

Update:

```bash
pip install --upgrade git+https://github.com/NuoBiT/odoo-xmlrpc-auth.git
```

Uninstall:

```bash
pip uninstall odoo-xmlrpc-auth
```

## CLI usage

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

### Examples

```bash
# Create a task
odoo-xmlrpc-auth --profile customer1 \
  '{"model":"project.task","method":"create","args":[{"name":"Bug: login broken","project_id":42}]}'

# Search with kwargs (fields, limit)
odoo-xmlrpc-auth --profile customer1 \
  '{"model":"project.task","method":"search_read","args":[[["project_id","=",5]]],"kwargs":{"fields":["name","stage_id"],"limit":10}}'

# Read a record
odoo-xmlrpc-auth --profile customer1 \
  '{"model":"res.partner","method":"read","args":[[1]]}'
```

## Library usage

Drop-in replacement for `xmlrpc.client.ServerProxy`. Just change the import
and add `profile=`:

```python
from odoo_xmlrpc_auth.client import ServerProxy

proxy = ServerProxy(profile="customer1")

# Same as xmlrpc.client, but db/uid/password are injected automatically
tasks = proxy.execute_kw("project.task", "search_read",
                         [[["project_id", "=", 5]]],
                         {"fields": ["name", "stage_id"], "limit": 10})

task_id = proxy.execute_kw("project.task", "create",
                           [{"name": "Bug: login broken", "project_id": 42}])

proxy.execute_kw("project.task", "write",
                 [[task_id], {"name": "Fixed"}])
```

Without `profile=`, it behaves exactly like the original `xmlrpc.client.ServerProxy`.

There's also a simpler functional API:

```python
from odoo_xmlrpc_auth import connect

execute = connect("customer1")
tasks = execute("project.task", "search_read",
                [[["project_id", "=", 5]]],
                {"fields": ["name"], "limit": 10})
```

## Configure a profile

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

The tool refuses to run if the config directory or files are accessible by
group or others (like `ssh` does with `~/.ssh/`).

## Security model

| Data | Leaves your machine? |
|---|---|
| Odoo credentials | No — read locally from `~/.config/` |
| API call parameters | Yes — sent to Odoo via XML-RPC |
| API results | Yes — returned from Odoo via XML-RPC |

The wrapper is like `psql` reading `~/.pgpass` — credentials stay local,
only the queries go over the wire.

## Prerequisites

- **python3 >= 3.8** (uses only stdlib: `xmlrpc.client`, `configparser`, `json`, `argparse`)
- No pip dependencies
