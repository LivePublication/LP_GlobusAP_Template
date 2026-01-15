from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
VERSION = "1.0.0"


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Failed to parse JSON from {path.name}: {exc}")
    return {}


def load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"Failed to parse YAML from {path.name}: {exc}")
    return {}


def validate_zenodo() -> None:
    path = REPO_ROOT / ".zenodo.json"
    data = load_json(path)
    required = ["title", "description", "license", "version", "creators"]
    for key in required:
        if key not in data or not data[key]:
            fail(f".zenodo.json missing required field: {key}")
    creators = data.get("creators", [])
    for creator in creators:
        orcid = creator.get("orcid", "")
        if not orcid:
            continue
        if "http" in orcid or "orcid.org" in orcid:
            fail(".zenodo.json ORCID must be bare digits (no URL)")
    if data.get("version") != VERSION:
        fail(".zenodo.json version must be 1.0.0")


def validate_codemeta() -> None:
    path = REPO_ROOT / "codemeta.json"
    data = load_json(path)
    if data.get("version") != VERSION:
        fail("codemeta.json version must be 1.0.0")


def validate_citation() -> None:
    path = REPO_ROOT / "CITATION.cff"
    data = load_yaml(path)
    if not isinstance(data, dict):
        fail("CITATION.cff is not valid YAML mapping")
    if data.get("version") != VERSION:
        fail("CITATION.cff version must be 1.0.0")


def validate_rocrate() -> None:
    path = REPO_ROOT / "ro-crate-metadata.json"
    data = load_json(path)
    graph = data.get("@graph", [])
    if not isinstance(graph, list):
        fail("ro-crate-metadata.json missing @graph list")

    ids = []
    for entry in graph:
        entry_id = entry.get("@id")
        if entry_id:
            ids.append(entry_id)
    duplicates = {item for item in ids if ids.count(item) > 1}
    if duplicates:
        fail(f"ro-crate-metadata.json contains duplicate @id values: {sorted(duplicates)}")

    root = next((e for e in graph if e.get("@id") in ("./", "")), None)
    if root is None:
        fail("ro-crate-metadata.json missing root dataset (@id './')")

    has_part = root.get("hasPart", [])
    part_ids = []
    if isinstance(has_part, list):
        for part in has_part:
            if isinstance(part, dict):
                part_ids.append(part.get("@id", ""))
            else:
                part_ids.append(str(part))
    elif isinstance(has_part, dict):
        part_ids.append(has_part.get("@id", ""))

    for part_id in part_ids:
        if not part_id:
            continue
        if part_id.startswith("#"):
            continue
        if "://" in part_id or part_id.startswith("http"):
            fail(f"ro-crate hasPart should use relative paths for local files: {part_id}")
        if Path(part_id).is_absolute():
            fail(f"ro-crate hasPart should not use absolute paths: {part_id}")
        if part_id.startswith("./"):
            relative_path = part_id[2:]
        else:
            relative_path = part_id
        if not (REPO_ROOT / relative_path).exists():
            fail(f"ro-crate hasPart path does not exist: {part_id}")


def print_checklist() -> None:
    print("\nMaintainer checklist:")
    print("- Confirm the quickstart steps are accurate for your deployment.")
    print("- Confirm the Apache-2.0 license matches the intended licensing.")
    print("- Confirm Zenodo GitHub integration is enabled for this repository.")
    print("- Create a GitHub release/tag v1.0.0 for DOI minting.")
    print("- After DOI minting, update metadata files with the DOI and release a patch.")


def main() -> None:
    validate_zenodo()
    validate_codemeta()
    validate_citation()
    validate_rocrate()
    print("Metadata validation passed.")
    print_checklist()


if __name__ == "__main__":
    main()

