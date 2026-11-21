#!/usr/bin/env python3
"""Static consistency checks for docker-compose.yml (no Docker required).

This is NOT a substitute for `docker compose config` / `docker compose up`; it catches the
mistakes that are cheap to detect: dangling references, undefined variables, exposed ports,
missing healthchecks, and a violated network-isolation rule.

Usage: python infrastructure/scripts/check_compose.py   (exit code 1 on any problem)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(:?[-?][^}]*)?\}")
OPTIONAL_HEALTHCHECK = {"qdrant"}  # opt-in profile, reserved for post-MVP


def env_example_keys() -> set[str]:
    keys = set()
    for line in (ROOT / ".env.example").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            keys.add(line.split("=", 1)[0])
    return keys


def walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for v in node.values():
            yield from walk_strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from walk_strings(v)


def main() -> int:
    compose = yaml.safe_load((ROOT / "docker-compose.yml").read_text())
    services: dict = compose["services"]
    declared_networks = set(compose.get("networks", {}))
    declared_volumes = set(compose.get("volumes", {}))
    known_env = env_example_keys()
    problems: list[str] = []

    for name, svc in services.items():
        # depends_on targets exist
        deps = svc.get("depends_on", {})
        for dep in deps if isinstance(deps, list) else deps.keys():
            if dep not in services:
                problems.append(f"{name}: depends_on unknown service '{dep}'")

        # networks declared, and every service is on at least one
        nets = svc.get("networks", [])
        if not nets:
            problems.append(f"{name}: not attached to any explicit network")
        for net in nets:
            if net not in declared_networks:
                problems.append(f"{name}: uses undeclared network '{net}'")

        # named volumes declared
        for vol in svc.get("volumes", []):
            source = str(vol).split(":", 1)[0]
            if not source.startswith((".", "/", "~")) and source not in declared_volumes:
                problems.append(f"{name}: uses undeclared volume '{source}'")

        # host ports must be loopback-only
        for port in svc.get("ports", []):
            if not str(port).startswith("127.0.0.1:"):
                problems.append(f"{name}: port '{port}' is not bound to 127.0.0.1")

        # build context + Dockerfile exist
        build = svc.get("build")
        if build:
            ctx = ROOT / (build if isinstance(build, str) else build.get("context", "."))
            if not (ctx / "Dockerfile").is_file():
                problems.append(f"{name}: no Dockerfile in build context {ctx.relative_to(ROOT)}")

        # healthcheck present
        if "healthcheck" not in svc and name not in OPTIONAL_HEALTHCHECK:
            problems.append(f"{name}: no healthcheck")

        # every ${VAR} without a default must be documented in .env.example
        for text in walk_strings(svc):
            for var, modifier in VAR.findall(text):
                has_default = bool(modifier) and modifier.startswith((":-", "-"))
                if not has_default and var not in known_env:
                    problems.append(f"{name}: ${{{var}}} is not defined in .env.example")

    # Isolation rule from docs/security.md: the worker must not share a network with data stores.
    worker_nets = set(services["browser-worker"].get("networks", []))
    for data_store in ("postgres", "redis", "qdrant"):
        shared = worker_nets & set(services[data_store].get("networks", []))
        if shared:
            problems.append(f"browser-worker shares network {sorted(shared)} with {data_store}")

    if problems:
        print("FAIL: docker-compose.yml problems found:")
        for p in problems:
            print(f"  - {p}")
        return 1
    print(f"OK: {len(services)} services, {len(declared_networks)} networks checked.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
