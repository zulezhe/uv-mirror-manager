"""Entry point for python -m uvm."""

import sys

# Fix Windows console encoding for Chinese output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

from uvm.cli import app

if __name__ == "__main__":
    app()
