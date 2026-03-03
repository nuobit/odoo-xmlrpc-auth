import configparser
import os
import stat
import xmlrpc.client

_SECTION = "odoo"
_REQUIRED_KEYS = ("url", "db", "user", "password")


class ConfigError(Exception):
    """Raised when a config file is missing, malformed, or insecure."""


class AuthError(Exception):
    """Raised when XML-RPC authentication fails."""


def _check_permissions(path, fd=None):
    mode = (os.fstat(fd) if fd is not None else os.stat(path)).st_mode
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        fix = "700" if stat.S_ISDIR(mode) else "600"
        raise ConfigError(
            f"{path} is accessible by others. Fix with: chmod {fix} {path}"
        )


def _read_config(profile):
    if os.sep in profile or profile.startswith("."):
        raise ConfigError(f"Invalid profile name: {profile}")
    config_dir = os.path.expanduser("~/.config/odoo-xmlrpc-auth")
    config_path = os.path.join(config_dir, f"{profile}.conf")

    try:
        _check_permissions(config_dir)
    except FileNotFoundError:
        pass

    parser = configparser.RawConfigParser()
    try:
        with open(config_path, encoding="utf-8") as f:
            _check_permissions(config_path, fd=f.fileno())
            parser.read_file(f)
    except FileNotFoundError:
        raise ConfigError(
            f"Config file not found: {config_path}\n"
            f"Create it with a [{_SECTION}] section and keys: "
            + ", ".join(_REQUIRED_KEYS)
        ) from None

    if not parser.has_section(_SECTION):
        raise ConfigError(f"Missing [{_SECTION}] section in {config_path}")

    config = dict(parser[_SECTION])
    missing = [k for k in _REQUIRED_KEYS if k not in config]
    if missing:
        raise ConfigError(
            f"Missing keys in {config_path}: {', '.join(missing)}"
        )

    config["url"] = config["url"].rstrip("/")
    return config


class ServerProxy(xmlrpc.client.ServerProxy):
    """Drop-in replacement for xmlrpc.client.ServerProxy with Odoo auth.

    When ``profile`` is given, reads credentials from the config file,
    authenticates, builds the URL automatically, and prepends
    db/uid/password to every ``execute_kw`` call.

    When ``profile`` is not given, behaves exactly like the original.

    Usage::

        from odoo_xmlrpc_auth.client import ServerProxy

        proxy = ServerProxy(profile="customer1")
        tasks = proxy.execute_kw("project.task", "search_read",
                                 [[["project_id", "=", 5]]],
                                 {"fields": ["name"], "limit": 10})
    """

    def __init__(self, uri=None, /, *args, profile=None, **kwargs):
        if profile is not None:
            config = _read_config(profile)
            url = config["url"]
            self._db = config["db"]

            kwargs.setdefault("allow_none", True)

            with xmlrpc.client.ServerProxy(
                f"{url}/xmlrpc/2/common", allow_none=True
            ) as common:
                self._uid = common.authenticate(
                    self._db, config["user"], config["password"], {}
                )

            if not self._uid:
                raise AuthError(
                    f"Authentication failed for {config['user']}@{self._db}"
                )

            self._password = config["password"]
            uri = f"{url}/xmlrpc/2/object"
        else:
            self._db = None
            self._uid = None
            self._password = None

        super().__init__(uri, *args, **kwargs)

    def execute_kw(self, *args, **kwargs):
        if self._db is not None:
            args = (self._db, self._uid, self._password, *args)
        return super().__getattr__("execute_kw")(*args, **kwargs)
