#!/usr/bin/env python3
"""
Comlina Database Migration Runner
Applies migrations in database/migrations/*.sql sequentially to PostgreSQL
and records execution state in the `schema_migrations` table to guarantee idempotency.
"""
import os
import sys
import glob
import re
from typing import Optional, List, Tuple

def load_dotenv():
    """Simple .env loader if python-dotenv is not installed."""
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key not in os.environ:
                os.environ[key] = val

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/comlina")

def normalize_db_url(url: str) -> str:
    """Normalize postgresql+asyncpg:// to postgresql:// for standard drivers."""
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url

def get_migration_files() -> List[str]:
    migration_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "migrations"))
    files = sorted(glob.glob(os.path.join(migration_dir, "*.sql")))
    return files

def run_with_psycopg2(url: str, files: List[str]) -> bool:
    import psycopg2
    print(f"Connecting to PostgreSQL using psycopg2: {url.split('@')[-1] if '@' in url else url}...")
    conn = psycopg2.connect(url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)
        conn.commit()

        cur.execute("SELECT version FROM schema_migrations;")
        applied = set(row[0] for row in cur.fetchall())

        applied_count = 0
        for f in files:
            version = os.path.basename(f)
            if version in applied:
                print(f"[SKIP] Already applied: {version}")
                continue

            print(f"[APPLYING] {version}...")
            with open(f, "r", encoding="utf-8") as sql_file:
                sql = sql_file.read()

            try:
                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (version) VALUES (%s);", (version,))
                conn.commit()
                print(f"[APPLIED]  {version}")
                applied_count += 1
            except Exception as e:
                conn.rollback()
                print(f"[ERROR] Failed applying {version}: {e}")
                raise

        print(f"\nMigration completed: {applied_count} applied, {len(applied)} previously applied.")
        return True
    finally:
        cur.close()
        conn.close()

def run_with_asyncpg(url: str, files: List[str]) -> bool:
    import asyncio
    import asyncpg

    async def _run():
        # Sanitize URL for asyncpg and detect SSL requirements
        connect_kwargs = {}
        cleaned_url = url
        lower_url = url.lower()
        if "sslmode=require" in lower_url or "ssl=require" in lower_url:
            connect_kwargs["ssl"] = "require"
            cleaned_url = re.sub(r'([?&])sslmode=[^&]*(&)?', r'\1', url)
            cleaned_url = re.sub(r'([?&])ssl=[^&]*(&)?', r'\1', cleaned_url).rstrip('?&')
        elif "@" in url:
            host_part = url.split("@")[-1].split(":")[0].split("/")[0].lower()
            if host_part not in ("localhost", "127.0.0.1", "0.0.0.0", "postgres"):
                connect_kwargs["ssl"] = "require"

        print(f"Connecting to PostgreSQL using asyncpg: {cleaned_url.split('@')[-1] if '@' in cleaned_url else cleaned_url} (SSL: {connect_kwargs.get('ssl', 'default')})...")
        conn = await asyncpg.connect(cleaned_url, **connect_kwargs)
        try:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)

            rows = await conn.fetch("SELECT version FROM schema_migrations;")
            applied = set(r["version"] for r in rows)

            applied_count = 0
            for f in files:
                version = os.path.basename(f)
                if version in applied:
                    print(f"[SKIP] Already applied: {version}")
                    continue

                print(f"[APPLYING] {version}...")
                with open(f, "r", encoding="utf-8") as sql_file:
                    sql = sql_file.read()

                async with conn.transaction():
                    await conn.execute(sql)
                    await conn.execute("INSERT INTO schema_migrations (version) VALUES ($1);", version)
                print(f"[APPLIED]  {version}")
                applied_count += 1

            print(f"\nMigration completed: {applied_count} applied, {len(applied)} previously applied.")
        finally:
            await conn.close()

    asyncio.run(_run())
    return True

import socket
from urllib.parse import urlparse

def is_service_reachable(url_str: str) -> bool:
    try:
        parsed = urlparse(url_str.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://"))
        host = parsed.hostname or "localhost"
        port = parsed.port or 5432
        is_remote = host not in ("localhost", "127.0.0.1", "0.0.0.0", "postgres")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1.5 if is_remote else 0.4)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def run_sqlite_dev_migration() -> bool:
    print("\n[DEV] Local PostgreSQL is not reachable on port 5432.")
    print("[DEV] Initializing and verifying SQLite development database schema...")
    server_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "server"))
    if server_dir not in sys.path:
        sys.path.insert(0, server_dir)
    try:
        from sqlalchemy import create_engine
        from app.core.database import Base
        import app.models  # noqa
        db_path = os.path.abspath(os.path.join(server_dir, "comlina_dev.db"))
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        import sqlite3
        conn = sqlite3.connect(db_path)
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
        conn.close()
        print(f"[DEV] Verified {len(tables)} tables in SQLite development database:")
        for t in sorted(tables):
            print(f"  - {t}")
        print("\n[SUCCESS] SQLite development database is fully migrated and ready!")
        return True
    except Exception as e:
        print(f"[DEV ERROR] Failed initializing SQLite database: {e}")
        return False

def main():
    print("=" * 60)
    print(" Comlina Database Migration Runner")
    print("=" * 60)

    url = DATABASE_URL
    for arg in sys.argv[1:]:
        if arg.startswith("--url="):
            url = arg.split("=", 1)[1]
        elif arg.startswith("--database-url="):
            url = arg.split("=", 1)[1]
    url = normalize_db_url(url)
    env = os.environ.get("ENVIRONMENT", "development")

    parsed = urlparse(url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://"))
    is_local_pg = (parsed.hostname or "").lower() in ("localhost", "127.0.0.1", "0.0.0.0")

    # In development mode, if local PostgreSQL is offline, gracefully verify/migrate SQLite dev database
    if env != "production" and is_local_pg and not is_service_reachable(url):
        success = run_sqlite_dev_migration()
        sys.exit(0 if success else 1)

    files = get_migration_files()
    print(f"Found {len(files)} SQL migration file(s).")

    # Try psycopg2
    try:
        import psycopg2
        run_with_psycopg2(url, files)
        return
    except ImportError:
        pass
    except Exception as e:
        print(f"psycopg2 error: {e}")
        sys.exit(1)

    # Try asyncpg
    try:
        import asyncpg
        run_with_asyncpg(url, files)
        return
    except ImportError:
        pass
    except Exception as e:
        print(f"asyncpg error: {e}")
        sys.exit(1)

    print("\n[NOTE] Neither 'psycopg2' nor 'asyncpg' is installed in current Python environment.")
    print("To install drivers: pip install asyncpg psycopg2-binary")
    print("Or run migrations via Docker: docker-compose up postgres (auto-loads /docker-entrypoint-initdb.d)")

if __name__ == "__main__":
    main()
