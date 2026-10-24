# scripts/repair_paused_automations.py
import argparse
import asyncio
import sys
from pathlib import Path

# Ensure repo root and server directory are in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SERVER_DIR = REPO_ROOT / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

try:
    from server.app.core.database import SessionLocal
    from server.app.models import Automation, InstagramAccount
except ImportError:
    from app.core.database import SessionLocal
    from app.models import Automation, InstagramAccount

from sqlalchemy import select, update, func


async def repair_automations(apply: bool = False):
    """
    Finds and resumes orphaned PAUSED automations that belong to CONNECTED accounts
    and lack a valid _pause_reason marker.
    Runs in dry-run mode unless --apply is explicitly specified.
    """
    async with SessionLocal() as db:
        stmt = (
            select(Automation.id, Automation.instagram_account_id, Automation.flow_definition)
            .join(InstagramAccount, Automation.instagram_account_id == InstagramAccount.id)
            .where(
                Automation.status == "PAUSED",
                InstagramAccount.connection_status == "CONNECTED"
            )
        )
        result = await db.execute(stmt)
        candidates = result.all()

        orphans = []
        for auto_id, acc_id, flow_def in candidates:
            flow = flow_def if isinstance(flow_def, dict) else {}
            # An orphaned automation is one that was paused during disconnection
            # but never resumed, and has no active _pause_reason recorded.
            if "_pause_reason" not in flow:
                orphans.append((auto_id, acc_id, flow))

        print(f"Found {len(orphans)} paused automations for active accounts.")
        for auto_id, acc_id, _ in orphans:
            print(f" - Automation: {auto_id} (Account: {acc_id})")

        if apply and orphans:
            for auto_id, acc_id, flow in orphans:
                clean_flow = {k: v for k, v in flow.items() if k != "_pause_reason"}
                await db.execute(
                    update(Automation)
                    .where(Automation.id == auto_id)
                    .values(
                        status="ACTIVE",
                        flow_definition=clean_flow,
                        updated_at=func.now()
                    )
                )
            await db.commit()
            print("Successfully resumed orphaned automations.")
        elif not apply and orphans:
            print("Dry-run complete. Run with --apply to resume these automations.")
        else:
            print("No orphaned automations found to repair.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Repair orphaned PAUSED automations for active accounts")
    parser.add_argument("--apply", action="store_true", help="Apply changes to the database (default: dry-run)")
    args = parser.parse_args()
    asyncio.run(repair_automations(apply=args.apply))
