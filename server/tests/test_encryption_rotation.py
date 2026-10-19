# server/tests/test_encryption_rotation.py
"""
Unit and integration tests for Work Item 10:
- MultiFernet encryption and decryption with key rotation
- Primary key encryption enforcement
- Secondary/fallback key decryption
- rotate_token re-encryption to primary key
- scripts/reencrypt_tokens.py CLI utility execution in dry-run and apply modes
"""

import base64
import os
import uuid
import pytest
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings
from app.core.encryption import (
    encrypt_token,
    decrypt_token,
    rotate_token,
    _normalize_key,
)
from scripts.reencrypt_tokens import reencrypt_all_tokens
from app.core.database import AsyncSessionLocal
from app.models import InstagramAccount, Workspace


def _generate_valid_fernet_key() -> str:
    return Fernet.generate_key().decode("utf-8")


class TestMultiFernetRotation:
    def test_single_key_roundtrip(self):
        token = "test_instagram_token_xyz123"
        encrypted = encrypt_token(token)
        assert encrypted != token
        decrypted = decrypt_token(encrypted)
        assert decrypted == token

    def test_multi_key_rotation_decryption(self, monkeypatch):
        primary_key = _generate_valid_fernet_key()
        secondary_key = _generate_valid_fernet_key()
        tertiary_key = _generate_valid_fernet_key()

        # Configure multiple keys: primary first, followed by secondaries
        monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEY", primary_key)
        monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEYS", f"{secondary_key},{tertiary_key}")

        token_a = "token_encrypted_under_secondary"
        token_b = "token_encrypted_under_tertiary"

        # Encrypt token_a using secondary key directly
        sec_fernet = Fernet(_normalize_key(secondary_key))
        sec_ciphertext = sec_fernet.encrypt(token_a.encode("utf-8")).decode("utf-8")

        # Encrypt token_b using tertiary key directly
        tert_fernet = Fernet(_normalize_key(tertiary_key))
        tert_ciphertext = tert_fernet.encrypt(token_b.encode("utf-8")).decode("utf-8")

        # MultiFernet decrypt_token should successfully decrypt both
        assert decrypt_token(sec_ciphertext) == token_a
        assert decrypt_token(tert_ciphertext) == token_b

    def test_encrypt_always_uses_primary_key(self, monkeypatch):
        primary_key = _generate_valid_fernet_key()
        secondary_key = _generate_valid_fernet_key()

        monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEY", primary_key)
        monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEYS", secondary_key)

        token = "fresh_token_12345"
        encrypted = encrypt_token(token)

        # Primary key alone MUST be able to decrypt it
        prim_fernet = Fernet(_normalize_key(primary_key))
        assert prim_fernet.decrypt(encrypted.encode("utf-8")).decode("utf-8") == token

        # Secondary key alone MUST NOT be able to decrypt it
        sec_fernet = Fernet(_normalize_key(secondary_key))
        with pytest.raises(InvalidToken):
            sec_fernet.decrypt(encrypted.encode("utf-8"))

    def test_rotate_token_reencrypts_to_primary_key(self, monkeypatch):
        primary_key = _generate_valid_fernet_key()
        secondary_key = _generate_valid_fernet_key()

        monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEY", primary_key)
        monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEYS", secondary_key)

        original_token = "reencrypt_me_please"

        # Encrypt under secondary key
        sec_fernet = Fernet(_normalize_key(secondary_key))
        old_ciphertext = sec_fernet.encrypt(original_token.encode("utf-8")).decode("utf-8")

        # Before rotation: primary key cannot decrypt it
        prim_fernet = Fernet(_normalize_key(primary_key))
        with pytest.raises(InvalidToken):
            prim_fernet.decrypt(old_ciphertext.encode("utf-8"))

        # Rotate token
        new_ciphertext = rotate_token(old_ciphertext)
        assert new_ciphertext != old_ciphertext

        # After rotation: primary key CAN decrypt it!
        assert prim_fernet.decrypt(new_ciphertext.encode("utf-8")).decode("utf-8") == original_token


class TestReencryptTokensCLI:
    @pytest.mark.asyncio
    async def test_cli_dry_run_and_apply(self, monkeypatch):
        primary_key = _generate_valid_fernet_key()
        secondary_key = _generate_valid_fernet_key()

        monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEY", primary_key)
        monkeypatch.setattr(settings, "TOKEN_ENCRYPTION_KEYS", secondary_key)

        # Create temporary test workspace and Instagram account encrypted under secondary key
        async with AsyncSessionLocal() as db:
            ws = Workspace(name=f"Reencrypt Test {uuid.uuid4().hex[:6]}", slug=f"reenc-{uuid.uuid4().hex[:6]}")
            db.add(ws)
            await db.commit()
            await db.refresh(ws)

            sec_fernet = Fernet(_normalize_key(secondary_key))
            old_ciphertext = sec_fernet.encrypt(b"token_to_reencrypt").decode("utf-8")

            acc = InstagramAccount(
                workspace_id=ws.id,
                ig_user_id=f"test_ig_{uuid.uuid4().hex[:8]}",
                username="test_reencrypt_user",
                access_token_encrypted=old_ciphertext,
                is_active=True,
            )
            db.add(acc)
            await db.commit()
            await db.refresh(acc)
            acc_id = acc.id

        try:
            # 1. Run in dry-run mode filtering by workspace_id
            res_dry = await reencrypt_all_tokens(dry_run=True, batch_size=50, workspace_id=ws.id)
            assert res_dry == 0

            # Verify DB was NOT modified in dry-run mode
            async with AsyncSessionLocal() as db:
                refreshed = await db.get(InstagramAccount, acc_id)
                assert refreshed is not None
                assert refreshed.access_token_encrypted == old_ciphertext

            # 2. Run in apply mode filtering by workspace_id
            res_apply = await reencrypt_all_tokens(dry_run=False, batch_size=50, workspace_id=ws.id)
            assert res_apply == 0

            # Verify DB WAS updated in apply mode and is decryptable by primary key
            async with AsyncSessionLocal() as db:
                refreshed = await db.get(InstagramAccount, acc_id)
                assert refreshed is not None
                encrypted_val = refreshed.access_token_encrypted
                assert encrypted_val != old_ciphertext
                prim_fernet = Fernet(_normalize_key(primary_key))
                assert prim_fernet.decrypt(encrypted_val.encode("utf-8")) == b"token_to_reencrypt"

        finally:
            # Clean up test records
            async with AsyncSessionLocal() as db:
                acc_to_del = await db.get(InstagramAccount, acc_id)
                if acc_to_del:
                    await db.delete(acc_to_del)
                ws_to_del = await db.get(Workspace, ws.id)
                if ws_to_del:
                    await db.delete(ws_to_del)
                await db.commit()
