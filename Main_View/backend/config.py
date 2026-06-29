from __future__ import annotations

import tempfile
from pathlib import Path

MAIN_VIEW_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = MAIN_VIEW_DIR.parent
FRONTEND_DIR = MAIN_VIEW_DIR / "frontend"
INDEX_FILE = FRONTEND_DIR / "index.html"
RUNTIME_DIR = Path(tempfile.gettempdir()) / "suite-digital-fresnillo-web"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
