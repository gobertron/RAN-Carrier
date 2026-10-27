#!/usr/bin/env python3
"""Compatibility entry point for the current four-ship Australis validator.

Delegates geometry bindings, aircraft routes, speed profile, lift lighting
and internal-fit checks to validate_recovery. It does not test gameplay.
"""
import argparse
from pathlib import Path

from validate_recovery import validate

DEST = Path(__file__).resolve().parents[1] / "game-mod/RAN-Carrier-Australis-2030"


def main(destination: Path = DEST, stock_root: Path | None = None):
    """Preserve the former importable main(destination, stock_root) interface."""
    return validate(destination, stock_root)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEST,
                        help="Current Australis package directory")
    parser.add_argument("--stock-root", "--original", dest="stock_root", type=Path,
                        help="StreamingAssets/original for stock reference checks")
    args = parser.parse_args()
    main(args.destination, args.stock_root)
