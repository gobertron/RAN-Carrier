#!/usr/bin/env python3
"""One-command, self-contained correction for the first original RAN carrier.

The payload contains only our own three changed files. This script verifies
the entire installed first release before it backs up and replaces that mod.
No RADF, Workshop, User Data, or original game files are modified.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import os
import shutil
import sys
import tempfile
import zlib
from pathlib import Path


MOD_NAME = "RAN-Carrier-Original-1959"
OLD_SIGNATURE = "36eafe2df181c37c5395fd060e95b11bbfc8f0996e85d1ce3573bbf09dbbb62c"
NEW_SIGNATURE = "717a549f06ef12b9fdc87b4802b3fcf2c6065b1d223f902e2abcd19946e88e07"
EXPECTED_PATCH_HASHES = {
    "README.txt": "cdc3f4ee21dc98f9c33f8a7e94031cdbd51ccefa724c8b034e791a117e656efc",
    "vessels/ran_cv_melbourne_1959.ini": "d84368eb5a7712ddc867b9181d15bb837e4a1d7fa1a1f31d02084c23c15ed00f",
    "ships/ran_cvl_melbourne_1959/ran_cvl_melbourne_1959.obj": "f65b247999818ea1593f15abe8ab160ea4d5ebfc59b28f360879fa139af4380b",
}
# Generated from the repository's original model and config. Each value is
# zlib-compressed file bytes encoded in base64, populated before publishing.
PAYLOAD: dict[str, str] = {
    'README.txt': (
        'eNpVkMFuGzEMRO/7FfMB3kWLooe0J6NBbk0TJ0XPtETvEtGKAinZ3b+vbJ96HZDzZuawf8YPMhM2/DKZJVPC54ev'
        'D3gxrVq3wsP/+tJS2uGUZF7qGDl8YGZdudoGyhFfPo0kFoxOFYEKBanbNBxajJ2wastdVjMOVTR/68pZ8gzfvPLq'
        'aM7QzFhJ8ngX70/DRerSAeC/JUk3RVGXq8eNmjRQGvUWFCv7Mg3PisP+8Qlq0Lp0+B+1D1+0IHLhHDmHbcJvZ+/E'
        'tOHYJNWxv78x4UUvbMNZvPXaWqoEv3H2zatRkh7klGiGsWuzwD7hfWH05phNW4H40HLR0hJVjt+RqOWw7PpD0DPb'
        'toNzdrW77YWpaHZk5oiZVsbrfhoexemYGD09NEX85HTstD7PO3vFkU9q3NdcC9l1xOsdR6m9cRKv0/APDjirLA=='
    ),
    'vessels/ran_cv_melbourne_1959.ini': (
        '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'
    ),
    'ships/ran_cvl_melbourne_1959/ran_cvl_melbourne_1959.obj': (
        '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'
        'ul/54f8CjHK+Jg=='
    ),
}


def fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files_in(root: Path) -> dict[str, str]:
    if root.is_symlink():
        raise ValueError(f"Refusing symlinked mod folder: {root}")
    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Refusing symlink in mod folder: {path}")
        if path.is_file():
            files[str(path.relative_to(root))] = fingerprint(path)
    return files


def signature(files: dict[str, str]) -> str:
    content = "".join(f"{name}\0{digest}\n" for name,digest in sorted(files.items()))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def game_running() -> bool:
    # Proton process names vary slightly between installations.
    for path in Path("/proc").glob("[0-9]*/comm"):
        try:
            name = path.read_text(encoding="utf-8").strip().lower()
        except (OSError, UnicodeError):
            continue
        if name in {"sea power.exe", "seapower.exe"}:
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--game-root", type=Path,
        default=Path.home() / ".local/share/Steam/steamapps/common/Sea Power",
        help="Override the Sea Power installation path for another Steam library",
    )
    args = parser.parse_args()
    assets = args.game_root / "Sea Power_Data/StreamingAssets"
    destination = assets / MOD_NAME
    try:
        print("[  0%] Checking original RAN carrier installation")
        if game_running():
            raise ValueError("Sea Power appears to be running. Close it fully, then rerun this script.")
        if not assets.is_dir() or not destination.is_dir():
            raise FileNotFoundError(f"Installed prototype not found: {destination}")
        installed = files_in(destination)
        current = signature(installed)
        if current == NEW_SIGNATURE:
            print(f"[100%] Already corrected: {destination}")
            return 0
        if current != OLD_SIGNATURE:
            raise ValueError(
                "Installed prototype differs from the exact first release. "
                "No files changed; send this message and the folder listing for review."
            )
        if set(PAYLOAD) != set(EXPECTED_PATCH_HASHES):
            raise ValueError("The embedded correction is incomplete")
        decoded: dict[str, bytes] = {}
        for relative, encoded in PAYLOAD.items():
            content = zlib.decompress(base64.b64decode(encoded, validate=True))
            if hashlib.sha256(content).hexdigest() != EXPECTED_PATCH_HASHES[relative]:
                raise ValueError(f"Embedded correction failed verification: {relative}")
            decoded[relative] = content
        print("[ 25%] First release and correction verified")

        with tempfile.TemporaryDirectory(prefix=".ran-carrier-fix-", dir=assets) as work:
            staged = Path(work) / MOD_NAME
            shutil.copytree(destination, staged)
            for relative, content in decoded.items():
                (staged / relative).write_bytes(content)
            if signature(files_in(staged)) != NEW_SIGNATURE:
                raise ValueError("Corrected staging folder failed whole-package verification")
            print("[ 50%] Corrected package staged and verified")

            backup_root = Path.home() / "Downloads/RAN-Carrier-Original-1959-backups"
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = Path(tempfile.mkdtemp(prefix="before-rudder-fix-", dir=backup_root)) / MOD_NAME
            shutil.copytree(destination, backup)
            if signature(files_in(backup)) != OLD_SIGNATURE:
                raise ValueError("Backup failed verification; original installation has not changed")
            print(f"[ 75%] Backup verified: {backup}")

            held = Path(work) / "previous"
            os.rename(destination, held)
            try:
                os.rename(staged, destination)
                if signature(files_in(destination)) != NEW_SIGNATURE:
                    raise ValueError("Installed package failed verification")
            except (OSError, ValueError):
                if destination.exists():
                    shutil.rmtree(destination)
                os.rename(held, destination)
                raise

        print(f"[100%] Corrected original RAN carrier: {destination}")
        print("[UNCHANGED] RADF, Workshop, original game files and User Data")
        print("[NEXT] Leave RADF enabled as before; restart Sea Power and open a new blank mission.")
        return 0
    except (OSError, ValueError, binascii.Error, zlib.error) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
