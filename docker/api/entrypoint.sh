#!/bin/sh
set -e

echo "Starting Enterprise AI Assistant API..."
echo "  Provider : ${LLM_PROVIDER:-openai}"
echo "  Workers  : ${APP_WORKERS:-2}"
echo "  Database : ${POSTGRES_HOST:-postgres}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-enterprise_ai}"

exec uvicorn app.main:app \
    --host "${APP_HOST:-0.0.0.0}" \
    --port "${APP_PORT:-8000}" \
    --workers "${APP_WORKERS:-2}" \
    --proxy-headers \
    --forwarded-allow-ips="*"
