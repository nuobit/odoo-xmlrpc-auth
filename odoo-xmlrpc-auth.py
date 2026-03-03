#!/usr/bin/env python3
"""Minimal CLI proxy for Odoo XML-RPC calls.

Injects credentials from ~/.config/odoo-xmlrpc-auth/<profile>.conf
so they never appear in command history or process arguments.
Takes a single JSON matching execute_kw's signature — the tool only adds auth.

Usage:
    odoo-xmlrpc-auth --profile <name> '<json>'

Examples:
    odoo-xmlrpc-auth --profile customer1 '{"model":"project.task","method":"create","args":[{"name":"Bug"}]}'
    odoo-xmlrpc-auth --profile customer1 '{"model":"project.task","method":"search_read","args":[[["project_id","=",5]]],"kwargs":{"fields":["name"],"limit":10}}'
"""

import argparse
import configparser
import json
import os
import stat
import sys
import xmlrpc.client

SECTION = "odoo"
REQUIRED_KEYS = ("url", "db", "user", "password")


def check_permissions(path, fd=None):
    """Refuse to run if path is accessible by group or others."""
    mode = (os.fstat(fd) if fd is not None else os.stat(path)).st_mode
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        print(
            f"Error: {path} is accessible by others. "
            f"Fix with: chmod {'700' if stat.S_ISDIR(mode) else '600'} {path}",
            file=sys.stderr,
        )
        sys.exit(1)


def read_config(profile):
    """Read credentials from ~/.config/odoo-xmlrpc-auth/<profile>.conf."""
    config_dir = os.path.expanduser("~/.config/odoo-xmlrpc-auth")
    config_path = os.path.join(config_dir, f"{profile}.conf")

    if os.path.isdir(config_dir):
        check_permissions(config_dir)

    parser = configparser.ConfigParser()
    try:
        with open(config_path, encoding="utf-8") as f:
            check_permissions(config_path, fd=f.fileno())
            parser.read_file(f)
    except FileNotFoundError:
        print(f"Error: config file not found: {config_path}", file=sys.stderr)
        print(
            f"Create it with a [{SECTION}] section and keys: "
            + ", ".join(REQUIRED_KEYS),
            file=sys.stderr,
        )
        sys.exit(1)

    if not parser.has_section(SECTION):
        print(
            f"Error: missing [{SECTION}] section in {config_path}", file=sys.stderr
        )
        sys.exit(1)

    config = dict(parser[SECTION])
    missing = [k for k in REQUIRED_KEYS if k not in config]
    if missing:
        print(
            f"Error: missing keys in {config_path}: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)

    return config


def main():
    parser = argparse.ArgumentParser(
        description="Odoo XML-RPC proxy — injects credentials transparently",
    )
    parser.add_argument(
        "--profile", required=True, help="profile name (matches <name>.conf)"
    )
    parser.add_argument("payload", help="JSON with model, method, args, kwargs")
    args = parser.parse_args()

    config = read_config(args.profile)

    try:
        call = json.loads(args.payload)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    url = config["url"].rstrip("/")
    db = config["db"]

    try:
        uid = xmlrpc.client.ServerProxy(
            f"{url}/xmlrpc/2/common", allow_none=True
        ).authenticate(db, config["user"], config["password"], {})
        if not uid:
            print("Error: authentication failed", file=sys.stderr)
            sys.exit(1)

        result = xmlrpc.client.ServerProxy(
            f"{url}/xmlrpc/2/object", allow_none=True
        ).execute_kw(
            db, uid, config["password"],
            call["model"], call["method"], call.get("args", []),
            call.get("kwargs", {}),
        )
    except xmlrpc.client.Fault as e:
        print(f"Error: {e.faultString}", file=sys.stderr)
        sys.exit(1)
    except (ConnectionRefusedError, OSError) as e:
        print(f"Error: cannot connect to {url}: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result))


if __name__ == "__main__":
    main()
