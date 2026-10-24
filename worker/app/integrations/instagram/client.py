# worker/app/integrations/instagram/client.py
# Re-exported from server.app.integrations.instagram.client (single source of truth)
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from server.app.integrations.instagram.client import *
