#!/usr/bin/env python3
"""Install the original RAN Melbourne prototype as its own Sea Power mod.

The installer only reads the packaged mod and writes a single new local mod
folder. It does not modify RADF, original game assets, or User Data.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
from pathlib import Path


GAME = Path("/home/aram/.local/share/Steam/steamapps/common/Sea Power")
MOD_NAME = "RAN-Carrier-Original-1959"
SOURCE = Path(__file__).resolve().parents[1] / "game-mod" / MOD_NAME
OLD_BRIDGE = Path.home() / "Downloads/RAN-Melbourne-1959-bridge-backups/active.json"
KNOWN_PRIOR_SIGNATURES = {
    # Initial 25-file prototype, published in PR #1 on 9 October 2026.
    "36eafe2df181c37c5395fd060e95b11bbfc8f0996e85d1ce3573bbf09dbbb62c",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def listed_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Package contains a symlink: {path}")
        if path.is_file():
            files[str(path.relative_to(root))] = digest(path)
    return files


def signature(files: dict[str, str]) -> str:
    content = "".join(f"{name}\0{digest}\n" for name,digest in sorted(files.items()))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=GAME)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--upgrade", action="store_true", help="Back up and replace the known first prototype")
    args = parser.parse_args()
    assets = args.game_root / "Sea Power_Data/StreamingAssets"
    destination = assets / MOD_NAME
    try:
        if OLD_BRIDGE.exists():
            raise ValueError(
                "The earlier User Data bridge is still active. First close Sea Power and run "
                "python3 ~/Downloads/bridge-ran-melbourne-1959.py --undo; then rerun this installer."
            )
        if not assets.is_dir():
            raise FileNotFoundError(f"Game StreamingAssets folder missing: {assets}")
        if not args.source.is_dir():
            raise FileNotFoundError(f"Original carrier package missing: {args.source}")
        originals = listed_files(args.source)
        required = {
            "_info.ini", "language_en/vessel_names.ini",
            "vessels/ran_cv_melbourne_1959.ini",
            "vessels/ran_cv_melbourne_1959_variants.ini",
            "ships/ran_cvl_melbourne_1959/ran_cvl_melbourne_1959.obj",
        }
        if not required <= originals.keys():
            raise ValueError("Package is incomplete: " + ", ".join(sorted(required - originals.keys())))
        prior = None
        if destination.is_symlink():
            raise ValueError(f"Installed mod folder must not be a symlink: {destination}")
        if destination.exists():
            if not destination.is_dir():
                raise FileExistsError(f"A file occupies {destination}")
            prior = listed_files(destination)
            if prior == originals:
                print(f"[OK] Original carrier mod already installed: {destination}")
                return 0
            if not args.upgrade:
                raise FileExistsError(f"An older or changed mod occupies {destination}. Use --upgrade for the known first release.")
            if signature(prior) not in KNOWN_PRIOR_SIGNATURES:
                raise ValueError("Installed folder differs from the published first release; refusing to overwrite your changes.")
        with tempfile.TemporaryDirectory(prefix=".ran-original-stage-", dir=assets) as work:
            stage = Path(work) / MOD_NAME
            shutil.copytree(args.source, stage)
            if listed_files(stage) != originals:
                raise ValueError("Copied package did not match its source")
            if prior is not None:
                backups = Path.home() / "Downloads/RAN-Carrier-Original-1959-backups"
                backups.mkdir(parents=True, exist_ok=True)
                backup = Path(tempfile.mkdtemp(prefix="before-rudder-fix-", dir=backups)) / MOD_NAME
                shutil.copytree(destination, backup)
                if listed_files(backup) != prior:
                    raise ValueError("Previous installation backup failed verification")
                held = Path(work) / "previous"
                os.rename(destination, held)
                try:
                    os.rename(stage, destination)
                except OSError:
                    os.rename(held, destination)
                    raise
                print(f"[BACKUP] Previous mod: {backup}")
                print(f"[OK] Updated original RAN carrier mod: {destination}")
            else:
                os.rename(stage, destination)
                print(f"[OK] Installed original RAN carrier mod: {destination}")
        print(f"[CHECK] {len(originals)} package files verified")
        print("[UNCHANGED] RADF Workshop files, original game files, User Data")
        print("[NEXT] Enable RAN Carrier Original 1959 Prototype in Mod Manager and restart Sea Power.")
        print("       The old RAN Melbourne 1959 Carrier Test can be disabled.")
    except (OSError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
