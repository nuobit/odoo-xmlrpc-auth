import argparse
import json
import sys
import xmlrpc.client

from . import __version__
from .client import ServerProxy
from .config import AuthError, ConfigError


def die(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Odoo XML-RPC proxy — injects credentials transparently",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--profile", required=True, help="profile name (matches <name>.conf)"
    )
    parser.add_argument("payload", help="JSON with model, method, args, kwargs")
    args = parser.parse_args()

    try:
        call = json.loads(args.payload)
    except json.JSONDecodeError as e:
        die(f"invalid JSON: {e}")

    for key in ("model", "method"):
        if key not in call:
            die(f"missing '{key}' in JSON payload")

    try:
        proxy = ServerProxy(profile=args.profile)
        result = proxy.execute_kw(
            call["model"], call["method"],
            call.get("args", []), call.get("kwargs", {}),
        )
    except (ConfigError, AuthError) as e:
        die(e)
    except xmlrpc.client.Fault as e:
        die(e.faultString)
    except OSError as e:
        die(e)

    print(json.dumps(result))
