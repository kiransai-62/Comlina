# server/tests/test_ci_security.py
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_dependabot_config_valid_and_comprehensive():
    dependabot_path = REPO_ROOT / ".github" / "dependabot.yml"
    assert dependabot_path.exists(), ".github/dependabot.yml must exist"

    data = yaml.safe_load(dependabot_path.read_text(encoding="utf-8"))
    assert data.get("version") == 2, "Dependabot version must be 2"

    updates = data.get("updates", [])
    assert len(updates) >= 4, "Dependabot must configure at least pip, npm, github-actions, and docker"

    ecosystems = {u.get("package-ecosystem") for u in updates}
    assert "pip" in ecosystems, "Dependabot must monitor pip dependencies"
    assert "npm" in ecosystems, "Dependabot must monitor npm dependencies"
    assert "github-actions" in ecosystems, "Dependabot must monitor github-actions"
    assert "docker" in ecosystems, "Dependabot must monitor docker configurations"


def test_security_audit_workflow_configured():
    workflow_path = REPO_ROOT / ".github" / "workflows" / "security-audit.yml"
    assert workflow_path.exists(), ".github/workflows/security-audit.yml must exist"

    content = workflow_path.read_text(encoding="utf-8")
    data = yaml.safe_load(content)

    jobs = data.get("jobs", {})
    assert "gitleaks" in jobs, "security-audit.yml must include a gitleaks job"
    assert "pip-audit" in jobs, "security-audit.yml must include a pip-audit job"
    assert "npm-audit" in jobs, "security-audit.yml must include an npm-audit job"
    assert "trivy" in jobs, "security-audit.yml must include a trivy job"


def test_ci_workflow_runs_client_tests():
    ci_path = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    assert ci_path.exists(), ".github/workflows/ci.yml must exist"

    content = ci_path.read_text(encoding="utf-8")
    assert "npm --prefix client test" in content, "CI workflow must run client unit tests"
