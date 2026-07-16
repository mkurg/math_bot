FROM python:3.14.5-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system bot && adduser --system --ingroup bot bot
COPY pyproject.toml requirements.lock ./
RUN pip install --upgrade pip==26.1.1 && pip install --requirement requirements.lock

COPY . .
RUN chown -R bot:bot /app
USER bot

CMD ["python", "-m", "app.main"]
