#!/usr/bin/env python3
"""Install or safely withdraw the independent Australis Sea Power prototype.

This script only creates or moves StreamingAssets/RAN-Carrier-Australis-2030.
It does not touch Workshop, RADF, User Data, or the game's original assets.
Run with Sea Power closed. Python's standard library is sufficient.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from validate_australis_2030_mod import main as validate

MOD_NAME = "RAN-Carrier-Australis-2030"
PACKAGE = Path(__file__).resolve().parents[1] / "game-mod" / MOD_NAME
DEFAULT_GAME = Path.home() / ".local/share/Steam/steamapps/common/Sea Power"
DEFAULT_BACKUPS = Path.home() / "Downloads/RAN-Carrier-Australis-2030-backups"


def fingerprints(folder: Path) -> dict[str, str]:
    """Reject links and hash every regular package file for copy verification."""
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError(f"Expected a real directory: {folder}")
    result = {}
    for entry in folder.rglob("*"):
        if entry.is_symlink():
            raise ValueError(f"A symlink is present: {entry}")
        if not (entry.is_file() or entry.is_dir()):
            raise ValueError(f"A special file is present: {entry}")
        if entry.is_file():
            result[entry.relative_to(folder).as_posix()] = hashlib.sha256(entry.read_bytes()).hexdigest()
    return result


def backup_existing(target: Path, backup_root: Path) -> Path:
    """Copy and verify a backup before moving the installed folder away."""
    if backup_root.is_symlink():
        raise ValueError(f"Backup folder must not be a symlink: {backup_root}")
    backup_root.mkdir(parents=True, exist_ok=True)
    old = fingerprints(target)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S-%f")
    path = backup_root / stamp / MOD_NAME
    path.parent.mkdir()
    try:
        shutil.copytree(target, path)
        if fingerprints(path) != old:
            raise ValueError("The withdrawal backup failed hash verification")
    except Exception:
        shutil.rmtree(path.parent)
        raise
    return path


def run(game: Path, source: Path, backups: Path, remove: bool) -> None:
    assets = game / "Sea Power_Data/StreamingAssets"
    target = assets / MOD_NAME
    print("[  0%] Checking the Sea Power location")
    if not assets.is_dir() or assets.is_symlink():
        raise FileNotFoundError(f"StreamingAssets directory missing: {assets}")
    if not (assets / "original/vessels/usn_cvn_nimitz.ini").is_file():
        raise FileNotFoundError("Expected the original Nimitz carrier INI in this Sea Power installation")
    if target.is_symlink():
        raise ValueError(f"Refusing a linked mod folder: {target}")
    if remove:
        if not target.exists():
            print(f"[OK] No {MOD_NAME} installation found")
            return
        if not target.is_dir():
            raise ValueError(f"The mod path is not a directory: {target}")
        if backups.resolve().is_relative_to(assets.resolve()):
            raise ValueError("The backup folder must be outside StreamingAssets")
        backup = backup_existing(target, backups)
        print(f"[ 75%] Backup verified: {backup}")
        if fingerprints(target) != fingerprints(backup):
            raise ValueError("The installed files changed while backing up; keeping the installation")
        shutil.rmtree(target)
        print(f"[100%] Withdrawn {MOD_NAME}; backup: {backup}")
        return

    print("[ 25%] Validating the independent package")
    original = fingerprints(source)
    if not original:
        raise ValueError("The package contains no files")
    validate(source)
    if target.exists():
        if not target.is_dir():
            raise ValueError(f"A file occupies the mod path: {target}")
        if fingerprints(target) == original:
            print(f"[100%] Already installed and verified: {target}")
            return
        raise FileExistsError(
            f"An existing {MOD_NAME} folder differs from this package: {target}. "
            "Back up and withdraw it with --remove before installing this version."
        )
    with tempfile.TemporaryDirectory(prefix=".ran-australis-stage-", dir=assets) as temp:
        staged = Path(temp) / MOD_NAME
        shutil.copytree(source, staged)
        if fingerprints(staged) != original:
            raise ValueError("The staged copy does not match the source")
        validate(staged)
        print(f"[ 75%] Verified {len(original)} staged package files")
        staged.rename(target)
    print(f"[100%] Installed the independent prototype: {target}")
    print("[UNCHANGED] RADF, Workshop, original game files, User Data")
    print("[NEXT] Enable RAN Australis 2030 Editor Prototype in Mod Manager; restart Sea Power.")
    print("       In a new blank mission, select Australia > CVN and search Australis.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=DEFAULT_GAME)
    parser.add_argument("--source", type=Path, default=PACKAGE,
                        help="Prebuilt package directory in this repository")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUPS)
    parser.add_argument("--remove", action="store_true",
                        help="Withdraw only this mod, retaining a verified backup")
    args = parser.parse_args()
    try:
        run(args.game_root, args.source, args.backup_dir, args.remove)
    except (OSError, ValueError, AssertionError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
