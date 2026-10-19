#!/usr/bin/env python3
"""
Comlina Token Re-Encryption CLI Tool
Rotates stored Instagram access tokens to the primary encryption key using MultiFernet.
Supports dry-run verification mode, batch processing, and zero secret leakage.
"""

import os
import sys
import uuid
import argparse
import asyncio
import logging
from pathlib import Path
from typing import Optional

# Setup paths to import server modules
ROOT_DIR = Path(__file__).resolve().parents[1]
SERVER_DIR = ROOT_DIR / "server"
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select, update

try:
    from app.core.config import settings
    from app.core.database import AsyncSessionLocal
    from app.models import InstagramAccount
    from app.core.encryption import (
        _normalize_key,
        decrypt_token,
        rotate_token,
    )
except ImportError:
    from server.app.core.config import settings  # type: ignore
    from server.app.core.database import AsyncSessionLocal  # type: ignore
    from server.app.models import InstagramAccount  # type: ignore
    from server.app.core.encryption import (  # type: ignore
        _normalize_key,
        decrypt_token,
        rotate_token,
    )

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("reencrypt_tokens")

async def reencrypt_all_tokens(
    dry_run: bool = True,
    batch_size: int = 100,
    workspace_id: Optional[uuid.UUID] = None,
    account_id: Optional[uuid.UUID] = None,
) -> int:
    """
    Scans all stored Instagram tokens, checks if they are encrypted with the primary key,
    and re-encrypts any tokens that were encrypted with secondary/fallback keys.
    Returns 0 on success, 1 on failure.
    """
    primary_key = settings.get_primary_encryption_key()
    all_keys = settings.get_encryption_keys()

    if not primary_key:
        logger.error("No primary encryption key found. Check TOKEN_ENCRYPTION_KEY(S).")
        return 1

    primary_fernet = Fernet(_normalize_key(primary_key))

    logger.info("=" * 60)
    logger.info("COMLINA TOKEN RE-ENCRYPTION UTILITY")
    logger.info("=" * 60)
    logger.info(f"Mode: {'DRY RUN (no database changes)' if dry_run else 'APPLY (modifying database)'}")
    logger.info(f"Active key rotation set: {len(all_keys)} configured keys")
    logger.info(f"Batch size: {batch_size}")
    if workspace_id:
        logger.info(f"Filter workspace_id: {workspace_id}")
    if account_id:
        logger.info(f"Filter account_id: {account_id}")
    logger.info("-" * 60)

    total_processed = 0
    already_primary = 0
    reencrypted_count = 0
    failed_count = 0
    empty_count = 0

    async with AsyncSessionLocal() as db:
        stmt = (
            select(InstagramAccount)
            .where(InstagramAccount.access_token_encrypted != "")
        )
        if workspace_id:
            stmt = stmt.where(InstagramAccount.workspace_id == workspace_id)
        if account_id:
            stmt = stmt.where(InstagramAccount.id == account_id)

        stmt = stmt.execution_options(yield_per=batch_size)
        res = await db.stream(stmt)
        accounts_to_update = []

        async for acc in res.scalars():
            total_processed += 1
            ciphertext = acc.access_token_encrypted
            if not ciphertext or ciphertext == "REVOKED":
                empty_count += 1
                continue

            # 1. Check if token is already decryptable by the primary key alone
            is_primary = False
            try:
                primary_fernet.decrypt(ciphertext.encode("utf-8"))
                is_primary = True
            except InvalidToken:
                is_primary = False
            except Exception:
                is_primary = False

            if is_primary:
                already_primary += 1
                continue

            # 2. Token is on a secondary/fallback key. Attempt rotation with MultiFernet
            try:
                # Decrypt verifies ciphertext against all keys in rotation
                plaintext = decrypt_token(ciphertext)
                if not plaintext:
                    empty_count += 1
                    continue

                # Re-encrypt under primary key
                new_ciphertext = rotate_token(ciphertext)

                # Sanity check: verify that primary key alone can decrypt the new ciphertext
                primary_fernet.decrypt(new_ciphertext.encode("utf-8"))

                reencrypted_count += 1
                if not dry_run:
                    acc.access_token_encrypted = new_ciphertext
                    accounts_to_update.append(acc)

                logger.info(
                    f"Account id={acc.id} (username=@{acc.username or 'unknown'}): "
                    f"{'[DRY RUN] Would re-encrypt' if dry_run else 'Re-encrypted'} under primary key."
                )

            except Exception as e:
                failed_count += 1
                logger.error(
                    f"Account id={acc.id} (username=@{acc.username or 'unknown'}): "
                    f"FAILED decryption under all configured keys: {e}"
                )

        if not dry_run and accounts_to_update:
            await db.commit()
            logger.info(f"Committed {len(accounts_to_update)} updated tokens to database.")

    logger.info("-" * 60)
    logger.info("SUMMARY:")
    logger.info(f"  Total accounts inspected:   {total_processed}")
    logger.info(f"  Already on primary key:     {already_primary}")
    logger.info(f"  Re-encrypted (or planned):  {reencrypted_count}")
    logger.info(f"  Empty or revoked tokens:    {empty_count}")
    logger.info(f"  Failed / unrecoverable:     {failed_count}")
    logger.info("=" * 60)

    if failed_count > 0:
        logger.warning(f"Re-encryption finished with {failed_count} decryption failures.")
        return 1

    logger.info("Re-encryption check completed successfully.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Re-encrypt Instagram access tokens under the primary key using MultiFernet."
    )
    parser.add_argument(
        "--apply",
        "--execute",
        dest="apply",
        action="store_true",
        default=False,
        help="Apply re-encryption changes to the database. (Default is dry-run)."
    )
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=True,
        help="Simulate re-encryption without modifying the database."
    )
    parser.add_argument(
        "--batch-size",
        dest="batch_size",
        type=int,
        default=100,
        help="Number of records to process per batch (default: 100)."
    )
    parser.add_argument(
        "--workspace-id",
        dest="workspace_id",
        type=str,
        default=None,
        help="Optional workspace ID to restrict re-encryption to."
    )
    parser.add_argument(
        "--account-id",
        dest="account_id",
        type=str,
        default=None,
        help="Optional Instagram account ID to restrict re-encryption to."
    )

    args = parser.parse_args()
    # If --apply was explicitly passed, dry_run is False
    is_dry_run = not args.apply

    ws_id = uuid.UUID(args.workspace_id) if args.workspace_id else None
    acc_id = uuid.UUID(args.account_id) if args.account_id else None

    try:
        exit_code = asyncio.run(
            reencrypt_all_tokens(
                dry_run=is_dry_run,
                batch_size=args.batch_size,
                workspace_id=ws_id,
                account_id=acc_id,
            )
        )
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error during token re-encryption: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
