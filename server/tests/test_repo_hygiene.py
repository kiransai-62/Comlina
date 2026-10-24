from pathlib import Path
import os
import re

REPO_ROOT = Path(__file__).resolve().parents[2]

def test_qa_and_session_artifacts_deleted():
    qa_login = REPO_ROOT / "client" / "public" / "qa-login.html"
    session_json = REPO_ROOT / "scripts" / "session.json"
    make_qa_login = REPO_ROOT / "scripts" / "make_qa_login.py"
    test_backend_checks = REPO_ROOT / "scripts" / "test_backend_checks.py"

    assert not qa_login.exists(), f"Found forbidden QA backdoor file: {qa_login}"
    assert not session_json.exists(), f"Found forbidden credential session file: {session_json}"
    assert not make_qa_login.exists(), f"Found forbidden token-minting script: {make_qa_login}"
    assert not test_backend_checks.exists(), f"Found token-minting script: {test_backend_checks}"

def test_no_token_minting_scripts_in_scripts_directory():
    scripts_dir = REPO_ROOT / "scripts"
    if not scripts_dir.exists():
        return

    for script_file in scripts_dir.rglob("*.py"):
        content = script_file.read_text(encoding="utf-8", errors="ignore")
        assert "jwt.encode" not in content, f"Script {script_file} contains token-minting jwt.encode logic!"
        assert "SUPABASE_JWT_SECRET" not in content, f"Script {script_file} references SUPABASE_JWT_SECRET directly!"

def test_pre_commit_config_exists_with_gitleaks():
    pre_commit = REPO_ROOT / ".pre-commit-config.yaml"
    assert pre_commit.exists(), ".pre-commit-config.yaml is missing"
    content = pre_commit.read_text(encoding="utf-8")
    assert "gitleaks" in content.lower(), "gitleaks hook missing from .pre-commit-config.yaml"

def test_gitignore_contains_security_exclusions():
    gitignore = REPO_ROOT / ".gitignore"
    assert gitignore.exists(), ".gitignore is missing"
    content = gitignore.read_text(encoding="utf-8")
    
    required_patterns = [
        ".env*",
        "!.env.example",
        "*.db",
        "*.sqlite",
        "session*.json",
        ".next*",
        "__pycache__",
        ".venv",
        "node_modules",
    ]
    for pattern in required_patterns:
        assert pattern in content, f"Pattern {pattern} missing from .gitignore"
