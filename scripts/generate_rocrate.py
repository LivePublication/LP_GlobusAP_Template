from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from rocrate.model.contextentity import ContextEntity
from rocrate.model.person import Person
from rocrate.rocrate import ROCrate


TITLE = "LP_GlobusAP_Template (Thesis Artifact)"
DESCRIPTION = (
    "Template repository for building Globus Action Providers in the LivePublication "
    "ecosystem, intended to support step-level provenance capture and Distributed Step "
    "Crate (DSC) generation patterns in Globus-based distributed execution environments. "
    "It provides a scaffold (structure, configuration, and example components) for "
    "operationalizing the thesis provenance model contributions."
)
VERSION = "1.0.1"
LICENSE_URL = "https://spdx.org/licenses/Apache-2.0"
REPO_URL = "https://github.com/LivePublication/LP_GlobusAP_Template"
DOI_URL = "https://doi.org/10.5281/zenodo.18255331"


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    crate = ROCrate()
    crate.source = repo_root
    root = crate.root_dataset

    root["name"] = TITLE
    root["description"] = DESCRIPTION
    root["license"] = LICENSE_URL
    root["version"] = VERSION
    root["datePublished"] = datetime.now(timezone.utc).isoformat()
    root["identifier"] = DOI_URL

    author = Person(
        crate,
        "https://orcid.org/0000-0001-8260-231X",
        properties={"name": "Augustus Ellerm"},
    )
    crate.add(author)

    software = ContextEntity(
        crate,
        "software",
        properties={
            "@type": "SoftwareSourceCode",
            "name": TITLE,
            "description": DESCRIPTION,
            "license": LICENSE_URL,
            "version": VERSION,
            "codeRepository": REPO_URL,
            "programmingLanguage": "Python",
            "identifier": DOI_URL,
        },
    )
    crate.add(software)
    software["author"] = author
    root["mainEntity"] = software

    added_paths: set[str] = set()

    def add_path(rel_path: str) -> None:
        normalized = rel_path.rstrip("/")
        if normalized in added_paths:
            return
        abs_path = repo_root / normalized
        if not abs_path.exists():
            return
        if abs_path.is_dir():
            entity = crate.add_directory(source=abs_path, dest_path=normalized)
        else:
            entity = crate.add_file(source=abs_path, dest_path=normalized)
        added_paths.add(normalized)

    paths = [
        "README.md",
        "LICENSE",
        ".zenodo.json",
        "codemeta.json",
        "CITATION.cff",
        "requirements.txt",
        "app.py",
        "blueprint.py",
        "backend.py",
        "config.py",
        "scripts",
        "scripts/generate_rocrate.py",
        "scripts/validate_metadata.py",
        "input",
        "input/test.txt",
        "output",
        "output/test.txt",
        "crates",
        "method_resources",
        "scope_definitions",
        "scope_definitions/group.json",
        "scope_definitions/group_transfer.json",
    ]

    for path in paths:
        add_path(path)

    crate.write(repo_root)


if __name__ == "__main__":
    main()

