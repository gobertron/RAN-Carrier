#!/usr/bin/env python3
"""Collect read-only Sea Power logs after an Australis editor load error.

Close Sea Power first and run before restarting it, so Player.log still
contains the failed load. This tool writes only under the output directory.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import re
from datetime import datetime
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

MOD_NAME = "RAN-Carrier-Australis-2030"
GAME = Path.home() / ".local/share/Steam/steamapps/common/Sea Power"
PROTON_SUFFIX = Path(
    "steamapps/compatdata/1286220/pfx/drive_c/users/steamuser/"
    "AppData/LocalLow/Triassic Games/Sea Power"
)
MAX_LOG_BYTES = 8 * 1024 * 1024
KEYWORDS = ("VesselRudderSystem.init", "ran_cvn_australis_2030", "Australis", "Exception")


def tail(path: Path) -> bytes:
    with path.open("rb") as source:
        if path.stat().st_size > MAX_LOG_BYTES:
            source.seek(-MAX_LOG_BYTES, 2)
        return source.read()


def excerpt(name: str, body: bytes) -> str:
    lines = [html.unescape(re.sub(r"<[^>]*>", "", line)).strip()
             for line in body.decode("utf-8", "replace").splitlines()]
    hits = [index for index, line in enumerate(lines)
            if any(word.lower() in line.lower() for word in KEYWORDS)]
    # Recent errors are most useful; merge overlapping line windows.
    selected = set()
    for index in hits[-12:]:
        selected.update(range(max(0, index - 30), min(len(lines), index + 18)))
    if not selected:
        return f"{name}: no Australis/rudder/exception line in the collected tail\n"
    return f"{name}: context around {min(len(hits), 12)} recent matches\n" + "\n".join(
        f"{index + 1}: {lines[index][:1200]}" for index in sorted(selected) if lines[index]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=GAME)
    parser.add_argument("--output-dir", type=Path, default=Path.home() / "Downloads")
    args = parser.parse_args()
    assets = args.game_root / "Sea Power_Data/StreamingAssets"
    mod = assets / MOD_NAME
    print("[  0%] Checking Australis and Sea Power log locations")
    notes = [f"Game: {args.game_root}", f"Australis mod: {mod}"]
    for relative in ("_info.ini", "vessels/ran_cvn_australis_2030.ini",
                     "vessels/ran_cvn_australis_2030_variants.ini",
                     "ships/ran_cvn_australis_2030/ran_cvn_australis_2030.obj"):
        path = mod / relative
        notes.append(f"{relative}: sha256={hashlib.sha256(path.read_bytes()).hexdigest()}"
                     if path.is_file() else f"{relative}: MISSING")
    print("[ 25%] Installed package hashes recorded")

    locations = [
        Path.home() / ".local/share/Steam" / PROTON_SUFFIX,
        Path.home() / ".steam/steam" / PROTON_SUFFIX,
        Path.home() / ".config/unity3d/Triassic Games/Sea Power",
    ]
    found: list[tuple[str, bytes]] = []
    seen: set[Path] = set()
    for location in locations:
        for filename in ("Player.log", "Player-prev.log"):
            path = location / filename
            if path.is_file() and path.resolve() not in seen:
                seen.add(path.resolve())
                found.append((f"player/{len(found) + 1}-{filename}", tail(path)))
                notes.append(f"Player log: {path} ({path.stat().st_size} bytes)")
    print(f"[ 50%] Player logs collected: {len(found)}")

    sessions = args.game_root / "Sea Power_Data/Logs"
    if sessions.is_dir():
        latest = sorted(sessions.glob("*.html"), key=lambda p: p.stat().st_mtime,
                        reverse=True)[:2]
        for path in latest:
            found.append((f"sessions/{path.name}", tail(path)))
            notes.append(f"Session log: {path} ({path.stat().st_size} bytes)")
    print(f"[ 75%] Total logs collected: {len(found)}")
    if not found:
        print("[ERROR] No logs found; please provide the Sea Power Player.log location")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    suffix = datetime.now().strftime("%Y%m%d-%H%M%S")
    context = args.output_dir / f"RAN-Australis-error-context-{suffix}.txt"
    bundle = args.output_dir / f"RAN-Australis-editor-diagnostics-{suffix}.zip"
    context.write_text("\n".join(excerpt(name, body) for name, body in found),
                       encoding="utf-8")
    with ZipFile(bundle, "w", ZIP_DEFLATED) as archive:
        archive.writestr("metadata.txt", "\n".join(notes) + "\n")
        archive.write(context, "error-context.txt")
        for name, body in found:
            archive.writestr(name, body)
    with ZipFile(bundle) as archive:
        if archive.testzip() is not None:
            print("[ERROR] Diagnostic ZIP verification failed")
            return 1
    print(f"[100%] Excerpt: {context}")
    print(f"[100%] Diagnostic ZIP: {bundle}")
    print("[UNCHANGED] Game, Australis, RADF, Workshop and User Data")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
