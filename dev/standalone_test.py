import os
import tempfile
from pathlib import Path

from backend.standalone import create_app, initialize_auth

directory = tempfile.TemporaryDirectory(prefix='hum-standalone-browser-')
root = Path(directory.name)
initialize_auth(root / 'credentials/auth.json', 'isolated-browser-password-2026')
os.environ.pop('USAGE_MANAGER_SESSION_CONTENT', None)
os.environ.pop('USAGE_MANAGER_TOOL_CONTENT', None)
app = create_app(root / 'credentials/auth.json', root / 'usage.sqlite3', 'http://127.0.0.1:9120')
