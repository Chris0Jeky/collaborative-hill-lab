#!/usr/bin/env python3
"""Validate, preview and explicitly publish the repository's curated issue seeds."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO / "scripts" / "issue_seeds.json"
SEED_FIELDS = {
    "id",
    "title",
    "status",
    "lane",
    "rationale",
    "scope",
    "acceptance",
    "verification",
    "dependencies",
    "sources",
}


class SeedError(ValueError):
    """Invalid input or an unconfirmed GitHub operation."""


def string_list(value: Any, field: str, *, empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (not value and not empty):
        raise SeedError(f"{field} must be a {'possibly empty' if empty else 'nonempty'} list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise SeedError(f"{field} must contain nonempty strings")
    if len(value) != len(set(value)):
        raise SeedError(f"{field} contains duplicates")
    return value


def validate_sources(sources: list[str], root: Path) -> None:
    for source in sources:
        path = Path(source)
        if path.is_absolute() or ".." in path.parts or "\\" in source:
            raise SeedError(f"Source must be a repository-relative file: {source}")
        resolved = (root / path).resolve()
        if not resolved.is_relative_to(root.resolve()) or not resolved.is_file():
            raise SeedError(f"Missing or external source: {source}")


def validate_seed(item: Any, root: Path) -> None:
    if not isinstance(item, dict) or not item.keys() >= SEED_FIELDS:
        raise SeedError("Every seed must have all required fields")
    if item.keys() - SEED_FIELDS - {"issue_number"}:
        raise SeedError("Seed has unknown fields")
    for field in ("id", "title", "rationale"):
        if not isinstance(item[field], str) or not item[field].strip():
            raise SeedError(f"{field} must be a nonempty string")
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", item["id"]):
        raise SeedError(f"Invalid stable seed id: {item['id']}")
    if len(item["title"]) > 200 or "\n" in item["title"]:
        raise SeedError("Issue titles must be one line and at most 200 characters")
    if item["status"] not in ("active", "next", "owner-decision"):
        raise SeedError("Unknown seed status")
    if item["lane"] not in ("engineering", "research", "owner-decision"):
        raise SeedError("Unknown seed lane")
    if "issue_number" in item and (
        type(item["issue_number"]) is not int or item["issue_number"] <= 0
    ):
        raise SeedError("issue_number must be a positive integer")
    for field in ("scope", "acceptance", "verification", "sources", "dependencies"):
        string_list(item[field], field, empty=field == "dependencies")
    validate_sources(item["sources"], root)


def validate_manifest(data: Any, root: Path) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != {"version", "repository", "seeds"}:
        raise SeedError("Manifest must contain version, repository and seeds")
    if data["version"] != "chl-roadmap@1":
        raise SeedError("Unsupported seed manifest version")
    if not isinstance(data["repository"], str) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", data["repository"]
    ):
        raise SeedError("repository must be owner/name")
    seeds = data["seeds"]
    if not isinstance(seeds, list) or not 1 <= len(seeds) <= 8:
        raise SeedError("Keep the curated queue between one and eight seeds")
    for item in seeds:
        validate_seed(item, root)
    by_id = {item["id"]: item for item in seeds}
    numbers = [item["issue_number"] for item in seeds if "issue_number" in item]
    if len(by_id) != len(seeds) or len(numbers) != len(set(numbers)):
        raise SeedError("Seed ids and pinned issue numbers must be unique")
    for item in seeds:
        if not set(item["dependencies"]) <= by_id.keys():
            raise SeedError(f"Unknown dependency for {item['id']}")

    def visit(seed_id: str, trail: set[str]) -> None:
        if seed_id in trail:
            raise SeedError(f"Dependency cycle at {seed_id}")
        for dependency in by_id[seed_id]["dependencies"]:
            visit(dependency, trail | {seed_id})

    for seed_id in by_id:
        visit(seed_id, set())
    return data


def load_manifest(path: Path, root: Path) -> dict[str, Any]:
    return validate_manifest(json.loads(path.read_text(encoding="utf-8")), root)


def marker(seed_id: str) -> str:
    return f"<!-- chl-roadmap:{seed_id} -->"


def render_body(seed: dict[str, Any], repository: str) -> str:
    lines = [
        marker(seed["id"]),
        "",
        f"Roadmap lane: **{seed['lane']}**. Planning status: **{seed['status']}**.",
        "",
        "## Why",
        "",
        seed["rationale"],
    ]
    for field, heading in (
        ("scope", "Scope"),
        ("acceptance", "Acceptance criteria"),
        ("verification", "Verification"),
    ):
        lines.extend(["", f"## {heading}", ""])
        prefix = "- [ ] " if field == "acceptance" else "- "
        lines.extend(prefix + item for item in seed[field])
    lines.extend(["", "## Dependencies", ""])
    lines.extend(f"- `{item}`" for item in seed["dependencies"])
    if not seed["dependencies"]:
        lines.append("None.")
    lines.extend(["", "## Source", ""])
    lines.extend(
        f"- [{path}](https://github.com/{repository}/blob/main/{path})" for path in seed["sources"]
    )
    lines.extend(
        [
            "",
            "This is a curated roadmap item. Closing it retires this seed; "
            "the seeder never reopens or edits existing issues.",
            "",
        ]
    )
    return "\n".join(lines)


def plan_issues(data: dict[str, Any], issues: Any = None) -> list[dict[str, Any]]:
    if issues is not None and not isinstance(issues, list):
        raise SeedError("Issue snapshot must be a complete JSON array")
    existing = []
    for item in issues or []:
        if not isinstance(item, dict):
            raise SeedError("Malformed issue in snapshot")
        if "pull_request" in item:
            continue
        if (
            type(item.get("number")) is not int
            or item["number"] <= 0
            or item.get("state") not in ("open", "closed")
            or (item.get("body") is not None and not isinstance(item["body"], str))
        ):
            raise SeedError("Malformed issue number, state or body in snapshot")
        existing.append(item)
    rows = []
    for seed in data["seeds"]:
        row = {
            "id": seed["id"],
            "title": seed["title"],
            "status": seed["status"],
            "lane": seed["lane"],
            "body": render_body(seed, data["repository"]),
            "action": "unreconciled" if issues is None else "create",
        }
        matches = [
            item
            for item in existing
            if marker(seed["id"]) in (item.get("body") or "")
            or item["number"] == seed.get("issue_number")
        ]
        if len(matches) > 1:
            raise SeedError(f"Seed {seed['id']} matches multiple issues; reconcile manually")
        if matches:
            match = matches[0]
            if "issue_number" in seed and match["number"] != seed["issue_number"]:
                raise SeedError(f"Marker for {seed['id']} conflicts with its pinned issue number")
            row.update(action=f"existing-{match['state']}", issue_number=match["number"])
        elif issues is not None and "issue_number" in seed:
            raise SeedError(
                f"Pinned issue #{seed['issue_number']} was not found; refusing recreation"
            )
        rows.append(row)
    return rows


class GitHub:
    """Only list and create issues; never PATCH, reopen, comment or retry a POST."""

    def __init__(self, repository: str, token: str) -> None:
        self.repository = repository
        self.token = token

    def request(self, method: str, path: str, payload: Any = None) -> Any:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "chl-issue-seeder",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        body = None
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = Request(
            f"https://api.github.com/repos/{self.repository}/{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except (HTTPError, URLError, OSError, ValueError) as exc:
            # Do not echo tokens, response bodies or server-provided URLs into CI logs.
            code = exc.code if isinstance(exc, HTTPError) else type(exc).__name__
            raise SeedError(f"GitHub {method} failed ({code}); response unconfirmed") from exc

    def list_issues(self) -> list[dict[str, Any]]:
        result = []
        page = 1
        while True:
            batch = self.request("GET", f"issues?state=all&per_page=100&page={page}")
            if not isinstance(batch, list):
                raise SeedError("GitHub returned a malformed issue page")
            result.extend(batch)
            if len(batch) < 100:
                return result
            page += 1


def publish_issues(rows: list[dict[str, Any]], client: GitHub) -> bool:
    ok = True
    for row in rows:
        if row["action"] != "create":
            continue
        if not ok:
            row["action"] = "not-attempted"
            continue
        try:
            created = client.request("POST", "issues", {"title": row["title"], "body": row["body"]})
            if (
                not isinstance(created, dict)
                or type(created.get("number")) is not int
                or created["number"] <= 0
            ):
                raise SeedError("Creation response lacked a valid issue number")
            row.update(action="created", issue_number=created["number"])
        except SeedError as exc:
            row.update(action="unconfirmed", error=str(exc))
            ok = False
    return ok


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--check", action="store_true", help="Validate only; always offline")
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--remote", action="store_true", help="Read all open and closed GitHub issues"
    )
    source.add_argument(
        "--issues-file", type=Path, help="Preview against a complete saved issue array"
    )
    parser.add_argument(
        "--publish", action="store_true", help="Read GitHub then create missing seeds"
    )
    args = parser.parse_args(argv)
    if args.publish and (args.issues_file or args.check):
        parser.error("--publish cannot be combined with --issues-file or --check")
    try:
        data = load_manifest(args.manifest, REPO)
        if args.check:
            print(f"Valid {data['version']} manifest: {len(data['seeds'])} curated seeds")
            return 0
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
        if args.publish and not token:
            raise SeedError("Publishing requires GITHUB_TOKEN or GH_TOKEN")
        client = GitHub(data["repository"], token)
        issues = None
        mode = "offline-preview"
        if args.remote or args.publish:
            workflow_repo = os.environ.get("GITHUB_REPOSITORY")
            if workflow_repo and workflow_repo != data["repository"]:
                raise SeedError("Workflow repository does not match the seed manifest")
            issues = client.list_issues()
            mode = "publish" if args.publish else "remote-preview"
        elif args.issues_file:
            issues = json.loads(args.issues_file.read_text(encoding="utf-8"))
            mode = "snapshot-preview"
        rows = plan_issues(data, issues)
        ok = publish_issues(rows, client) if args.publish else True
        print(
            json.dumps(
                {
                    "version": "chl-issue-plan@1",
                    "repository": data["repository"],
                    "mode": mode,
                    "ok": ok,
                    "issues": rows,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0 if ok else 1
    except (SeedError, OSError, ValueError) as exc:
        print(f"Issue seed error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
