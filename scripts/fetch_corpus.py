"""Fetch the AdvaitaBench source corpus and record content hashes.

Downloads each entry in corpus/sources.yaml into corpus/raw/ (gitignored) and
writes corpus/manifest.json mapping id -> {url, sha256, bytes}. The hashes make
a run reproducible: task passages mined from the corpus can be traced to a
fixed source snapshot.

Usage:
    python -m scripts.fetch_corpus                # verified entries only
    python -m scripts.fetch_corpus --all          # include unverified paths
    python -m scripts.fetch_corpus --id taittiriya_bhasya
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "corpus" / "sources.yaml"
RAW_DIR = ROOT / "corpus" / "raw"
MANIFEST = ROOT / "corpus" / "manifest.json"


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "AdvaitaBench-corpus-fetch"})
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - fixed GRETIL host
        return resp.read()


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch AdvaitaBench source corpus")
    ap.add_argument("--all", action="store_true", help="Include entries marked verified: false")
    ap.add_argument("--id", default=None, help="Fetch a single source by id")
    args = ap.parse_args()

    spec = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))
    base = spec.get("base_url", "").rstrip("/")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}

    for src in spec.get("sources", []):
        if args.id and src["id"] != args.id:
            continue
        if not args.id and not args.all and not src.get("verified"):
            print(f"- skip {src['id']} (unverified; pass --all to fetch)")
            continue

        url = f"{base}/{src['path'].lstrip('/')}"
        try:
            data = _fetch(url)
        except Exception as exc:  # noqa: BLE001
            print(f"! {src['id']}: {exc}")
            continue

        suffix = ".htm" if src["path"].endswith((".htm", ".html")) else ".txt"
        dest = RAW_DIR / f"{src['id']}{suffix}"
        dest.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        manifest[src["id"]] = {
            "url": url, "sha256": digest, "bytes": len(data),
            "title": src.get("title", ""), "license": src.get("license", ""),
        }
        print(f"+ {src['id']}: {len(data):,} bytes  sha256:{digest[:12]}…  -> {dest.name}")

    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nManifest: {MANIFEST}")


if __name__ == "__main__":
    main()
