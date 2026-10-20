"""Vercel entrypoint importing WSGI application."""
from wsgi import app

# Expose app for Vercel Python serverless runtime
__all__ = ["app"]
