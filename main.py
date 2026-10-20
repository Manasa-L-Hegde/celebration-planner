"""Main entrypoint for Vercel, Gunicorn, and local execution."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
