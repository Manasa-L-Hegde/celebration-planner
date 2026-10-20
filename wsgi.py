"""WSGI entrypoint for Vercel, Gunicorn, and Cloud Run deployment."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
