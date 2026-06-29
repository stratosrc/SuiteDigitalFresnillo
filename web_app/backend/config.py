from __future__ import annotations

import tempfile
from pathlib import Path

WEB_APP_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = WEB_APP_DIR.parent
STATIC_DIR = WEB_APP_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"
RUNTIME_DIR = Path(tempfile.gettempdir()) / "suite-digital-fresnillo-web"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
