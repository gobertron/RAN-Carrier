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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=GAME)
    parser.add_argument("--source", type=Path, default=SOURCE)
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
        if destination.exists():
            if destination.is_dir() and listed_files(destination) == originals:
                print(f"[OK] Original carrier mod already installed: {destination}")
                return 0
            raise FileExistsError(
                f"A different mod already occupies {destination}. Move it to a backup first."
            )
        with tempfile.TemporaryDirectory(prefix=".ran-original-stage-", dir=assets) as work:
            stage = Path(work) / MOD_NAME
            shutil.copytree(args.source, stage)
            if listed_files(stage) != originals:
                raise ValueError("Copied package did not match its source")
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
