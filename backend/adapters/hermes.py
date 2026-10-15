import os
from pathlib import Path

from fastapi import HTTPException


def storage_path():
    configured = os.environ.get("USAGE_MANAGER_DB_PATH")
    if configured:
        return Path(configured).expanduser()
    try:
        from plugins.plugin_storage import plugin_data_dir
    except ImportError as error:
        raise RuntimeError("Hermes plugin_data_dir unavailable; configure a secure absolute USAGE_MANAGER_DB_PATH") from error
    return plugin_data_dir("hermes-usage-manager") / "usage.sqlite3"


def require_dashboard_admin(request):
    try:
        from hermes_cli.web_server import _require_token
    except ImportError as error:
        raise HTTPException(503, {"code": "HOST_AUTH_UNAVAILABLE", "message": "当前 Hermes 宿主认证适配不可用"}) from error
    _require_token(request)
