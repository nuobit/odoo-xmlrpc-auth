import configparser
import os
import stat
import xmlrpc.client

SECTION = "odoo"
REQUIRED_KEYS = ("url", "db", "user", "password")


class ConfigError(Exception):
    """Raised when a config file is missing, malformed, or insecure."""


class AuthError(Exception):
    """Raised when XML-RPC authentication fails."""


class RpcError(Exception):
    """Raised when an XML-RPC call returns a fault."""


def check_permissions(path, fd=None):
    """Refuse to run if path is accessible by group or others."""
    mode = (os.fstat(fd) if fd is not None else os.stat(path)).st_mode
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        fix = "700" if stat.S_ISDIR(mode) else "600"
        raise ConfigError(
            f"{path} is accessible by others. Fix with: chmod {fix} {path}"
        )


def read_config(profile):
    """Read credentials from ~/.config/odoo-xmlrpc-auth/<profile>.conf."""
    if os.sep in profile or profile.startswith("."):
        raise ConfigError(f"Invalid profile name: {profile}")
    config_dir = os.path.expanduser("~/.config/odoo-xmlrpc-auth")
    config_path = os.path.join(config_dir, f"{profile}.conf")

    try:
        check_permissions(config_dir)
    except FileNotFoundError:
        pass  # directory missing — open() below will raise FileNotFoundError

    parser = configparser.RawConfigParser()
    try:
        with open(config_path, encoding="utf-8") as f:
            check_permissions(config_path, fd=f.fileno())
            parser.read_file(f)
    except FileNotFoundError:
        raise ConfigError(
            f"Config file not found: {config_path}\n"
            f"Create it with a [{SECTION}] section and keys: "
            + ", ".join(REQUIRED_KEYS)
        ) from None

    if not parser.has_section(SECTION):
        raise ConfigError(f"Missing [{SECTION}] section in {config_path}")

    config = dict(parser[SECTION])
    missing = [k for k in REQUIRED_KEYS if k not in config]
    if missing:
        raise ConfigError(
            f"Missing keys in {config_path}: {', '.join(missing)}"
        )

    return config


def connect(profile):
    """Connect to an Odoo instance and return an execute_kw callable.

    Reads credentials from ~/.config/odoo-xmlrpc-auth/<profile>.conf,
    authenticates via XML-RPC, and returns a function with db/uid/password
    already injected.

    Usage::

        execute = connect("customer1")
        tasks = execute("project.task", "search_read",
                        [[["project_id", "=", 5]]],
                        {"fields": ["name"], "limit": 10})
    """
    config = read_config(profile)

    url = config["url"].rstrip("/")
    db = config["db"]

    uid = xmlrpc.client.ServerProxy(
        f"{url}/xmlrpc/2/common", allow_none=True
    ).authenticate(db, config["user"], config["password"], {})
    if not uid:
        raise AuthError(f"Authentication failed for {config['user']}@{db}")

    password = config["password"]
    proxy = xmlrpc.client.ServerProxy(
        f"{url}/xmlrpc/2/object", allow_none=True
    )

    def execute(model, method, args=None, kwargs=None):
        try:
            return proxy.execute_kw(
                db, uid, password, model, method,
                args if args is not None else [],
                kwargs if kwargs is not None else {},
            )
        except xmlrpc.client.Fault as e:
            raise RpcError(e.faultString) from e

    return execute
