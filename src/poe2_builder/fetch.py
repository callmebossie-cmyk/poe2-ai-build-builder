from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .sources import SOURCE_FILES


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_sources(cache_dir: Path, *, force: bool = False) -> Path:
    cache_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for source in SOURCE_FILES:
        destination = cache_dir / source.name
        if force or not destination.exists():
            temporary = destination.with_suffix(destination.suffix + ".part")
            request = urllib.request.Request(
                source.url,
                headers={"User-Agent": "poe2-ai-build-builder/0.1 source-fetcher"},
            )
            with urllib.request.urlopen(request, timeout=120) as response:
                temporary.write_bytes(response.read())
            temporary.replace(destination)
        records.append(
            {
                "file": source.name,
                "source": source.source,
                "version": source.version,
                "url": source.url,
                "sha256": sha256_file(destination),
                "bytes": destination.stat().st_size,
            }
        )
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": records,
    }
    manifest_path = cache_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def verify_manifest(cache_dir: Path) -> dict:
    manifest_path = cache_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Source manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for record in manifest["files"]:
        path = cache_dir / record["file"]
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")
        actual = sha256_file(path)
        if actual != record["sha256"]:
            raise ValueError(f"Checksum mismatch for {path.name}")
    return manifest

