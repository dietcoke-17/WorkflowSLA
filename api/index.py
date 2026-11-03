"""
WorkflowSLA: Vercel Serverless Entrypoint
Exports the FastAPI application for Vercel Serverless Python deployment.
"""
import sys
from pathlib import Path

# Ensure root directory is in Python path for Vercel execution environment
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from api.main import app
