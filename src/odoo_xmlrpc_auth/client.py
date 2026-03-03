import xmlrpc.client

from .config import AuthError, read_config


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
            config = read_config(profile)
            url = config["url"].rstrip("/")
            self._db = config["db"]

            kwargs.setdefault("allow_none", True)

            # Authenticate to get uid
            common = xmlrpc.client.ServerProxy(
                f"{url}/xmlrpc/2/common", **kwargs
            )
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
        return super().execute_kw(*args, **kwargs)
