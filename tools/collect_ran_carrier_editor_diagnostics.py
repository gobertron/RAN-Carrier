#!/usr/bin/env python3
"""Collect Sea Power logs for the original RAN carrier editor crash.

Run after closing Sea Power. The script reads logs and hashes our installed
carrier files; it does not edit the game, User Data, Workshop mods or RADF.
The resulting ZIP is written to Downloads for review.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import re
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


MOD_NAME = "RAN-Carrier-Original-1959"
GAME_REL = Path(".local/share/Steam/steamapps/common/Sea Power")
PROTON_REL = Path(
    "steamapps/compatdata/1286220/pfx/drive_c/users/steamuser/"
    "AppData/LocalLow/Triassic Games/Sea Power"
)
MAX_LOG_BYTES = 8 * 1024 * 1024


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tail(path: Path) -> bytes:
    with path.open("rb") as stream:
        if path.stat().st_size > MAX_LOG_BYTES:
            stream.seek(-MAX_LOG_BYTES, 2)
        return stream.read()


def readable_line(raw: str) -> str:
    return html.unescape(re.sub(r"<[^>]*>", "", raw)).strip()


def excerpt(name: str, contents: bytes) -> str:
    lines = [readable_line(line) for line in contents.decode("utf-8", "replace").splitlines()]
    hits = [i for i,line in enumerate(lines) if "VesselRudderSystem.init" in line]
    if not hits:
        return f"{name}: no VesselRudderSystem.init line in collected tail\n"
    i = hits[-1]
    start, end = max(0, i - 80), min(len(lines), i + 28)
    return f"{name}: last rudder exception, lines {start + 1}-{end}\n" + "\n".join(
        f"{n + 1}: {lines[n][:1200]}" for n in range(start,end) if lines[n]
    ) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, default=Path.home() / GAME_REL)
    parser.add_argument("--output-dir", type=Path, default=Path.home() / "Downloads")
    parser.add_argument("--proton-log-dir", type=Path, default=None)
    args = parser.parse_args()

    game = args.game_root
    mod = game / "Sea Power_Data/StreamingAssets" / MOD_NAME
    logdir = game / "Sea Power_Data/Logs"
    proton_paths = [Path.home() / ".steam/steam" / PROTON_REL,
                    Path.home() / ".local/share/Steam" / PROTON_REL]
    proton = args.proton_log_dir or next((p for p in proton_paths if p.is_dir()), proton_paths[0])

    print("[  0%] Checking carrier and log paths")
    notes = [f"Game: {game}", f"Carrier mod: {mod}", f"Session logs: {logdir}", f"Proton logs: {proton}"]
    for relative in ("_info.ini", "vessels/ran_cv_melbourne_1959.ini",
                     "vessels/ran_cv_melbourne_1959_variants.ini",
                     "ships/ran_cvl_melbourne_1959/ran_cvl_melbourne_1959.obj"):
        path = mod / relative
        notes.append(f"{relative}: sha256={digest(path)}" if path.is_file()
                     else f"{relative}: MISSING")
    print("[ 25%] Installed carrier file hashes recorded")

    found: list[tuple[str, bytes]] = []
    for name in ("Player.log", "Player-prev.log"):
        path = proton / name
        if path.is_file():
            found.append((f"proton/{name}", tail(path)))
            notes.append(f"{name}: {path} ({path.stat().st_size} bytes)")
    print(f"[ 50%] Proton logs collected: {sum(n.startswith('proton/') for n,_ in found)}")

    sessions = sorted(logdir.glob("*.html"), key=lambda path: path.stat().st_mtime, reverse=True)[:2] if logdir.is_dir() else []
    for path in sessions:
        found.append((f"sessions/{path.name}", tail(path)))
        notes.append(f"Session: {path} ({path.stat().st_size} bytes)")
    print(f"[ 75%] Latest game session logs collected: {len(sessions)}")
    if not found:
        print("[ERROR] No Sea Power logs found. Check the game path or whether it has launched.")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output = args.output_dir / f"RAN-carrier-editor-diagnostics-{stamp}.zip"
    excerpts = "\n".join(excerpt(name, body) for name,body in found)
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("metadata.txt", "\n".join(notes) + "\n")
        archive.writestr("rudder-error-context.txt", excerpts)
        for name,body in found:
            archive.writestr(name, body)
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            print("[ERROR] Diagnostic ZIP failed verification")
            return 1
    print(f"[100%] Diagnostics saved: {output}")
    print("[UNCHANGED] Sea Power, User Data, Workshop and RADF")
    print("[NEXT] Upload this ZIP for analysis of the failing vessel and mesh load.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
