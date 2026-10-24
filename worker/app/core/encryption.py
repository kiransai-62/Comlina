# worker/app/core/encryption.py
# Re-exported from server.app.core.encryption (single source of truth)
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from server.app.core.encryption import *
from server.app.core.encryption import _normalize_key, _get_fernet, _get_multi_fernet
