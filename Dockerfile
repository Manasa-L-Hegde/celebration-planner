FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    TRUST_PROXY=1

WORKDIR /srv
RUN useradd --system --uid 1001 appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application packages, modular services, prompts, and entrypoints
COPY app app
COPY services services
COPY prompts prompts
COPY main.py wsgi.py ./

USER appuser

# One process with several threads so the in-memory rate limiter and cache are shared.
CMD exec gunicorn --bind "0.0.0.0:${PORT}" --workers 1 --threads 8 --timeout 60 "app:create_app()"
