# server/tests/test_container_security.py
import re
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_docker_compose_dev_ports_bind_to_localhost():
    compose_path = REPO_ROOT / "docker-compose.yml"
    assert compose_path.exists(), "docker-compose.yml must exist"

    content = compose_path.read_text(encoding="utf-8")
    lines = content.splitlines()

    in_ports_block = False
    for line in lines:
        stripped = line.strip()
        if stripped == "ports:":
            in_ports_block = True
            continue
        if in_ports_block:
            if stripped.startswith("- "):
                port_mapping = stripped[2:].strip().strip("\"'")
                # Must start with 127.0.0.1:
                assert port_mapping.startswith("127.0.0.1:"), (
                    f"Port binding '{port_mapping}' in docker-compose.yml must bind to 127.0.0.1"
                )
            elif not stripped.startswith("#") and stripped:
                in_ports_block = False


def test_dockerfiles_have_pinned_images():
    dockerfiles = [
        REPO_ROOT / "server" / "Dockerfile",
        REPO_ROOT / "worker" / "Dockerfile",
        REPO_ROOT / "client" / "Dockerfile",
        REPO_ROOT / "infra" / "docker" / "server.Dockerfile",
        REPO_ROOT / "infra" / "docker" / "worker.Dockerfile",
        REPO_ROOT / "infra" / "docker" / "client.Dockerfile",
        REPO_ROOT / "infra" / "docker" / "nginx.Dockerfile",
    ]

    for df in dockerfiles:
        if not df.exists():
            continue
        content = df.read_text(encoding="utf-8")
        from_lines = [l.strip() for l in content.splitlines() if l.strip().startswith("FROM ")]
        for fl in from_lines:
            assert ":latest" not in fl, f"Unpinned :latest tag in {df}: {fl}"
            # Ensure major tags without minor/patch are not used (e.g., node:18-alpine, python:3.11-slim)
            assert not re.search(r"python:3\.\d+-slim\b", fl), f"Unpinned python slim tag in {df}: {fl}"
            assert not re.search(r"node:\d+-alpine\b", fl), f"Unpinned node alpine tag in {df}: {fl}"
            assert not re.search(r"nginx:\d+\.\d+-alpine\b", fl), f"Unpinned nginx alpine tag in {df}: {fl}"


def test_dockerfiles_enforce_non_root_user():
    dockerfiles = [
        REPO_ROOT / "server" / "Dockerfile",
        REPO_ROOT / "worker" / "Dockerfile",
        REPO_ROOT / "client" / "Dockerfile",
        REPO_ROOT / "infra" / "docker" / "server.Dockerfile",
        REPO_ROOT / "infra" / "docker" / "worker.Dockerfile",
        REPO_ROOT / "infra" / "docker" / "client.Dockerfile",
    ]

    for df in dockerfiles:
        if not df.exists():
            continue
        content = df.read_text(encoding="utf-8")
        has_user_directive = any(l.strip().startswith("USER ") for l in content.splitlines())
        assert has_user_directive, f"Dockerfile {df} must specify a non-root USER"


def test_prod_compose_no_insecure_defaults():
    prod_compose = REPO_ROOT / "docker-compose.prod.yml"
    if not prod_compose.exists():
        pytest.skip("docker-compose.prod.yml not present")

    content = prod_compose.read_text(encoding="utf-8")
    assert "comlina_redis_secret" not in content, "docker-compose.prod.yml contains hardcoded default secret"
