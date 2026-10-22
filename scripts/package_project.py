"""
Script to create a clean, security-hardened distribution archive (comlina_project.zip)
strictly under 10MB without any sensitive environment files, SQLite databases,
build caches, or test artifacts.
"""
import os
import zipfile

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_ZIP = os.path.join(PROJECT_ROOT, "comlina_project.zip")

# Exact directory names to skip anywhere in tree
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "env",
    "ENV",
    "__pycache__",
    ".pytest_cache",
    ".next",
    ".next_app",
    ".build_dist",
    "dist",
    "build",
    "out",
    "htmlcov",
    ".idea",
    ".vscode",
    "docker-data",
    "pgdata",
    "redisdata",
    "e2e_artifacts",
    "_archive",
    "logs",
}

# File extensions or specific filenames to skip
SKIP_EXTENSIONS = (
    ".pyc",
    ".pyo",
    ".pyd",
    ".tsbuildinfo",
    ".db",
    ".db-journal",
    ".sqlite",
    ".sqlite3",
    ".zip",
    ".log",
    ".DS_Store",
    ".swp",
    ".swo",
)

def should_include_file(rel_path: str) -> bool:
    norm_path = rel_path.replace("\\", "/")
    parts = norm_path.split("/")
    filename = parts[-1]

    # Check if any parent directory should be skipped
    for part in parts[:-1]:
        if part in SKIP_DIRS:
            return False

    # Skip files inside duplicate client/stores shim directory
    if norm_path.startswith("client/stores/"):
        return False

    # Check file extension
    for ext in SKIP_EXTENSIONS:
        if filename.endswith(ext):
            return False

    # Check environment files: only allow .env.example templates
    if filename.startswith(".env"):
        if filename in {".env.example", ".env.production.example"}:
            return True
        return False

    # Skip temporary or session keys
    if filename.startswith("session") and filename.endswith(".json"):
        return False
    if filename.endswith(".pem") or filename.endswith(".key"):
        return False

    return True

def create_archive():
    print(f"Creating archive at: {OUTPUT_ZIP}")
    included_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Prune directory recursion early
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, PROJECT_ROOT)

                if should_include_file(rel_path):
                    zipf.write(abs_path, rel_path)
                    included_count += 1
                    total_uncompressed_bytes += os.path.getsize(abs_path)

    zip_size_bytes = os.path.getsize(OUTPUT_ZIP)
    zip_size_mb = zip_size_bytes / (1024 * 1024)
    print(f"Archive created successfully!")
    print(f"  Files included: {included_count}")
    print(f"  Uncompressed size: {total_uncompressed_bytes / (1024 * 1024):.2f} MB")
    print(f"  Compressed ZIP size: {zip_size_mb:.2f} MB")
    assert zip_size_mb < 10.0, f"Error: Archive exceeds 10 MB limit ({zip_size_mb:.2f} MB)"

if __name__ == "__main__":
    create_archive()
