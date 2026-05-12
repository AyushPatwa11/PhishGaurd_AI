"""Entrypoint to run FastAPI inference service locally with Uvicorn."""
import os
import sys
import uvicorn

# Ensure project root is on path when invoked from the repository root
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.api_service.main import app


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
