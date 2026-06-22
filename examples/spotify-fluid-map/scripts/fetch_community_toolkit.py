#!/usr/bin/env python3
"""Fetch vetted community TouchDesigner tools into ignored runtime storage."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = EXAMPLE_ROOT / "community" / "community_toolkit.json"
DEFAULT_DEST = EXAMPLE_ROOT / "runtime" / "community"
GITHUB_API = "https://api.github.com"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run(cmd: list[str], cwd: Path | None = None) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed ({result.returncode}): {' '.join(cmd)}\n{detail}")
    return result.stdout.strip()


def safe_child(root: Path, name: str) -> Path:
    root_resolved = root.resolve()
    child = (root / name).resolve()
    if root_resolved != child and root_resolved not in child.parents:
        raise ValueError(f"Refusing path outside destination: {child}")
    return child


def repo_url(repo: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError(f"Expected GitHub owner/repo, got {repo!r}")
    return f"https://github.com/{repo}.git"


def api_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "touchdesigner-ai-brain-community-fetcher",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clone_args(entry: dict, dest: Path) -> list[str]:
    fetch = entry["fetch"]
    args = ["git", "clone", "--depth", "1"]
    ref = fetch.get("ref")
    if ref:
        args.extend(["--branch", ref])
    if fetch["mode"] == "git_sparse":
        args.extend(["--filter=blob:none", "--sparse"])
    args.extend([repo_url(fetch["repo"]), str(dest)])
    return args


def remove_existing(path: Path, force: bool) -> None:
    if not path.exists():
        return
    if not force:
        raise FileExistsError(f"{path} already exists; use --force to refresh it")
    shutil.rmtree(path)


def git_revision(path: Path) -> str:
    return run(["git", "-C", str(path), "rev-parse", "HEAD"])


@dataclass(frozen=True)
class FetchResult:
    id: str
    name: str
    category: str
    license: str
    source_url: str
    local_path: str
    status: str
    details: dict[str, object]


class ToolkitFetcher:
    def __init__(self, dest_root: Path, dry_run: bool = False, force: bool = False) -> None:
        self.dest_root = dest_root
        self.dry_run = dry_run
        self.force = force

    def fetch(self, entry: dict) -> FetchResult:
        mode = entry["fetch"]["mode"]
        dest = safe_child(self.dest_root, entry["id"])
        if mode == "github_release_asset":
            return self.fetch_release_asset(entry, dest)
        if mode in {"git_clone", "git_sparse"}:
            return self.fetch_git(entry, dest)
        return self.record_non_download(entry, dest, mode)

    def fetch_git(self, entry: dict, dest: Path) -> FetchResult:
        fetch = entry["fetch"]
        if self.dry_run:
            return result_for(entry, dest, "dry-run", {"mode": fetch["mode"]})
        remove_existing(dest, self.force)
        run(clone_args(entry, dest))
        if fetch["mode"] == "git_sparse":
            paths = [str(path) for path in fetch.get("paths", [])]
            run(["git", "-C", str(dest), "sparse-checkout", "set", "--no-cone", *paths])
        return result_for(
            entry,
            dest,
            "downloaded",
            {
                "mode": fetch["mode"],
                "repo": fetch["repo"],
                "ref": fetch.get("ref", ""),
                "revision": git_revision(dest),
            },
        )

    def fetch_release_asset(self, entry: dict, dest: Path) -> FetchResult:
        fetch = entry["fetch"]
        if self.dry_run:
            return result_for(entry, dest, "dry-run", {"mode": fetch["mode"]})

        remove_existing(dest, self.force)
        dest.mkdir(parents=True, exist_ok=True)
        asset = find_release_asset(fetch["repo"], fetch["tag"], fetch["asset"])
        output = dest / asset["name"]
        download_file(asset["browser_download_url"], output)
        return result_for(
            entry,
            dest,
            "downloaded",
            {
                "mode": fetch["mode"],
                "repo": fetch["repo"],
                "tag": fetch["tag"],
                "asset": asset["name"],
                "asset_url": asset["browser_download_url"],
                "size": asset["size"],
                "sha256": sha256_file(output),
            },
        )

    def record_non_download(self, entry: dict, dest: Path, mode: str) -> FetchResult:
        return result_for(entry, dest, "not-downloaded", {"mode": mode})


def find_release_asset(repo: str, tag: str, asset_name: str) -> dict:
    release = api_json(f"{GITHUB_API}/repos/{repo}/releases/tags/{tag}")
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            return asset
    names = ", ".join(asset.get("name", "") for asset in release.get("assets", []))
    raise ValueError(f"Asset {asset_name!r} not found in {repo} {tag}. Found: {names}")


def download_file(url: str, output: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "touchdesigner-ai-brain-community-fetcher"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        with tempfile.NamedTemporaryFile(delete=False, dir=output.parent) as tmp:
            tmp_path = Path(tmp.name)
            shutil.copyfileobj(response, tmp)
    tmp_path.replace(output)


def result_for(entry: dict, local_path: Path, status: str, details: dict[str, object]) -> FetchResult:
    return FetchResult(
        id=entry["id"],
        name=entry["name"],
        category=entry["category"],
        license=entry["license"],
        source_url=entry["source_url"],
        local_path=str(local_path),
        status=status,
        details=details,
    )


def select_entries(entries: list[dict], only: list[str], include_all: bool) -> list[dict]:
    if only:
        wanted = set(only)
        selected = [entry for entry in entries if entry["id"] in wanted]
        missing = sorted(wanted - {entry["id"] for entry in selected})
        if missing:
            raise ValueError(f"Unknown toolkit ids: {', '.join(missing)}")
        return selected
    if include_all:
        return [entry for entry in entries if entry["fetch"]["mode"] != "manual"]
    return [entry for entry in entries if entry.get("download_default") is True]


def print_list(entries: list[dict]) -> None:
    for entry in entries:
        default = "default" if entry.get("download_default") else "optional"
        mode = entry["fetch"]["mode"]
        print(f"{entry['id']:32} {default:8} {mode:22} {entry['license']:12} {entry['name']}")


def build_manifest(results: list[FetchResult]) -> dict[str, object]:
    return {
        "generated_at": utc_now(),
        "results": [result.__dict__ for result in results],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--only", action="append", default=[])
    parser.add_argument("--all", action="store_true", help="Fetch optional non-manual entries too.")
    parser.add_argument("--list", action="store_true", help="List toolkit entries and exit.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true", help="Delete and re-fetch existing entries.")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    registry = load_json(args.registry)
    entries = registry["entries"]
    if args.list:
        print_list(entries)
        return 0

    selected = select_entries(entries, args.only, args.all)
    fetcher = ToolkitFetcher(args.dest, dry_run=args.dry_run, force=args.force)
    results = [fetcher.fetch(entry) for entry in selected]
    manifest = build_manifest(results)
    write_json(args.dest / "manifest.json", manifest)
    for result in results:
        print(f"{result.status:14} {result.id} -> {result.local_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
