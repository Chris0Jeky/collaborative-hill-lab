"""Curated issue seeds must never turn a preview or a closed issue into new work."""

import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "seed_issues.py"


def module():
    assert SCRIPT.is_file(), "The preview-first issue seeder is not implemented"
    spec = importlib.util.spec_from_file_location("seed_issues_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def seed(seed_id="first", **overrides):
    result = {
        "id": seed_id,
        "title": f"Implement {seed_id}",
        "status": "next",
        "lane": "engineering",
        "rationale": "Make existing evidence easier to inspect.",
        "scope": ["One bounded change."],
        "acceptance": ["The result is visible and reproducible."],
        "verification": ["Run the relevant offline regression."],
        "dependencies": [],
        "sources": ["README.md"],
    }
    return result | overrides


def manifest(*seeds):
    return {
        "version": "chl-roadmap@1",
        "repository": "Chris0Jeky/collaborative-hill-lab",
        "seeds": list(seeds or [seed()]),
    }


def issue(number, seed_id="first", state="open", **overrides):
    return {
        "number": number,
        "state": state,
        "body": f"An existing discussion.\n<!-- chl-roadmap:{seed_id} -->",
    } | overrides


def test_shipped_manifest_has_unique_seeds_and_real_source_paths():
    mod = module()
    data = mod.load_manifest(REPO / "scripts" / "issue_seeds.json", REPO)
    assert 6 <= len(data["seeds"]) <= 8
    pinned = {item["id"]: item.get("issue_number") for item in data["seeds"]}
    assert {
        key: pinned[key]
        for key in ("experiment-catalog", "round-inspector", "run-monitor", "project-direction")
    } == {
        "experiment-catalog": 110,
        "round-inspector": 111,
        "run-monitor": 112,
        "project-direction": 113,
    }


@pytest.mark.parametrize(
    "change",
    [
        {"id": "bad marker -->"},
        {"acceptance": []},
        {"sources": ["missing.md"]},
        {"sources": ["../outside.md"]},
        {"dependencies": ["unknown"]},
        {"issue_number": True},
        {"unexpected": "typo"},
    ],
)
def test_invalid_manifest_fails_before_any_publication(change):
    mod = module()
    with pytest.raises(mod.SeedError):
        mod.validate_manifest(manifest(seed(**change)), REPO)


def test_dependency_cycles_are_rejected():
    mod = module()
    data = manifest(seed("first", dependencies=["second"]), seed("second", dependencies=["first"]))
    with pytest.raises(mod.SeedError, match="cycle"):
        mod.validate_manifest(data, REPO)


def test_existing_open_and_closed_are_never_created_again():
    mod = module()
    data = manifest(seed("first"), seed("second"), seed("third"))
    rows = mod.plan_issues(data, [issue(1), issue(2, "second", "closed")])
    assert [row["action"] for row in rows] == ["existing-open", "existing-closed", "create"]
    assert "<!-- chl-roadmap:third -->" in rows[2]["body"]
    assert "## Acceptance criteria" in rows[2]["body"]


def test_known_issue_number_survives_removed_marker():
    mod = module()
    rows = mod.plan_issues(manifest(seed(issue_number=110)), [issue(110, body="Edited body")])
    assert rows[0]["action"] == "existing-open"
    with pytest.raises(mod.SeedError, match="110"):
        mod.plan_issues(manifest(seed(issue_number=110)), [])


def test_duplicate_markers_stop_the_plan_instead_of_guessing():
    mod = module()
    with pytest.raises(mod.SeedError, match="multiple"):
        mod.plan_issues(manifest(), [issue(1), issue(2, state="closed")])


def test_pull_requests_do_not_consume_issue_markers():
    mod = module()
    rows = mod.plan_issues(manifest(), [issue(5, pull_request={"url": "unused"})])
    assert rows[0]["action"] == "create"


def test_remote_reconciliation_reads_beyond_first_page_and_includes_closed():
    mod = module()
    calls = []

    def request(method, path, payload=None):
        calls.append((method, path, payload))
        if path.endswith("&page=1"):
            return [issue(n, f"unrelated-{n}") for n in range(1, 101)]
        return [issue(101, state="closed")]

    client = mod.GitHub("Chris0Jeky/collaborative-hill-lab", "")
    client.request = request
    rows = mod.plan_issues(manifest(), client.list_issues())
    assert rows[0]["action"] == "existing-closed"
    assert len(calls) == 2
    assert all(method == "GET" and "state=all" in path for method, path, _ in calls)


def test_default_preview_is_offline_and_does_not_claim_dedupe(monkeypatch, capsys):
    mod = module()

    def no_network(*args, **kwargs):
        pytest.fail("Default preview made a network request")

    monkeypatch.setattr(mod.GitHub, "request", no_network)
    assert mod.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["mode"] == "offline-preview"
    assert all(row["action"] == "unreconciled" for row in result["issues"])


def test_snapshot_preview_only_reads_and_reports_closed(tmp_path, capsys):
    mod = module()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest()), encoding="utf-8")
    snapshot = tmp_path / "issues.json"
    snapshot.write_text(json.dumps([issue(2, state="closed")]), encoding="utf-8")
    assert mod.main(["--manifest", str(path), "--issues-file", str(snapshot)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["issues"][0]["action"] == "existing-closed"


def test_publish_requires_token_and_cannot_trust_an_offline_snapshot(monkeypatch, capsys):
    mod = module()
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.delenv("GH_TOKEN", raising=False)
    assert mod.main(["--publish"]) != 0
    assert "token" in capsys.readouterr().err.lower()
    with pytest.raises(SystemExit):
        mod.main(["--publish", "--issues-file", "snapshot.json"])


def test_partial_publication_failure_reports_confirmed_and_unconfirmed_results():
    mod = module()
    rows = mod.plan_issues(manifest(seed("first"), seed("second"), seed("third")), [])

    class Client:
        def request(self, method, path, payload=None):
            if payload["title"] == "Implement first":
                return {"number": 51}
            raise mod.SeedError("Connection closed; response unknown")

    ok = mod.publish_issues(rows, Client())
    assert not ok
    assert [row["action"] for row in rows] == ["created", "unconfirmed", "not-attempted"]
    assert rows[0]["issue_number"] == 51
    assert "response unknown" in rows[1]["error"]


def test_publish_does_not_modify_existing_discussions():
    mod = module()
    rows = mod.plan_issues(manifest(), [issue(8, state="closed")])

    class Client:
        def request(self, *args, **kwargs):
            pytest.fail("Existing issues must not be mutated")

    assert mod.publish_issues(rows, Client())
    assert rows[0]["action"] == "existing-closed"


@pytest.mark.parametrize("body", [False, 0, [], {}])
def test_malformed_issue_body_stops_reconciliation(body):
    mod = module()
    with pytest.raises(mod.SeedError, match="Malformed issue"):
        mod.plan_issues(manifest(), [issue(4, body=body)])


def test_create_request_has_exact_marker_and_unconfirmed_failures_are_nonzero(
    tmp_path, monkeypatch, capsys
):
    mod = module()
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest()), encoding="utf-8")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    received = []

    def request(self, method, path, payload=None):
        if method == "GET":
            return []
        received.append((method, path, payload))
        raise mod.SeedError("Publication response was lost")

    monkeypatch.setattr(mod.GitHub, "request", request)
    assert mod.main(["--manifest", str(path), "--publish"]) == 1
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] is False
    assert result["issues"][0]["action"] == "unconfirmed"
    assert len(received) == 1
    assert received[0][0:2] == ("POST", "issues")
    assert "<!-- chl-roadmap:first -->" in received[0][2]["body"]


def test_transport_uses_fixed_repository_and_redacts_error_payload(monkeypatch):
    from urllib.error import HTTPError

    mod = module()
    captured = []

    def reject(request, timeout):
        captured.append(request)
        raise HTTPError(request.full_url, 403, "secret response body", {}, None)

    monkeypatch.setattr(mod, "urlopen", reject)
    client = mod.GitHub("Chris0Jeky/collaborative-hill-lab", "secret-token")
    with pytest.raises(mod.SeedError) as caught:
        client.request("POST", "issues", {"title": "Title", "body": "Body"})
    request = captured[0]
    assert (
        request.full_url == "https://api.github.com/repos/Chris0Jeky/collaborative-hill-lab/issues"
    )
    assert request.get_method() == "POST"
    assert json.loads(request.data) == {"title": "Title", "body": "Body"}
    assert request.get_header("Authorization") == "Bearer secret-token"
    assert "403" in str(caught.value)
    assert "secret" not in str(caught.value)
