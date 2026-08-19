"""Posit Connect entry point for the Git-backed FastAPI application.

Created: 2026-08-19
"""

from app.main import create_app

app = create_app()
