# worker/app/jobs/process_comment.py
# Re-exported from server.app.jobs.process_comment (single source of truth)
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from server.app.jobs.process_comment import *
from server.app.jobs.process_comment import process_comment_job, _update_webhook_event
