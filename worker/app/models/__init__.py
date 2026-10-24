# worker/app/models/__init__.py
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

# Single source of truth is server.app.models
from server.app.models import (
    Base,
    User,
    Workspace,
    WorkspaceMember,
    InstagramAccount,
    Automation,
    AutomationVersion,
    Contact,
    Conversation,
    Message,
    WebhookEvent,
    AnalyticsEvent,
    PostUsage,
    PaymentOrder,
    AutomationRun,
    utc_now,
)

__all__ = [
    "Base",
    "User",
    "Workspace",
    "WorkspaceMember",
    "InstagramAccount",
    "Automation",
    "AutomationVersion",
    "Contact",
    "Conversation",
    "Message",
    "WebhookEvent",
    "AnalyticsEvent",
    "PostUsage",
    "PaymentOrder",
    "AutomationRun",
    "utc_now",
]
