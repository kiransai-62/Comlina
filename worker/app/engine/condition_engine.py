# worker/app/engine/condition_engine.py
# Re-exported from server.app.engine.condition_engine (single source of truth)
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from server.app.engine.condition_engine import *
from server.app.engine.condition_engine import ConditionEngine
