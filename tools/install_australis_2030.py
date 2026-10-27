#!/usr/bin/env python3
"""Compatibility entry point for the current verified Australis installer.

All arguments are handled by install_recovery, including package checksums,
the supported game version, AnchorChain dependencies, backup and rollback.
Use --help for its current options. Arbitrary legacy --source packages are
not supported because they would bypass the current verified release.
"""
from install_recovery import main


if __name__ == "__main__":
    raise SystemExit(main())
