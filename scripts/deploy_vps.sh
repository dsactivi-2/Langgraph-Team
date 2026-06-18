#!/usr/bin/env bash
set -euo pipefail

: "${VPS_HOST:?Set VPS_HOST, for example 203.0.113.10}"
: "${VPS_USER:?Set VPS_USER, for example deploy}"

VPS_PATH="${VPS_PATH:-/opt/langgraph-builder-team}"
SSH_TARGET="${VPS_USER}@${VPS_HOST}"

rsync -az --delete \
  --exclude ".git" \
  --exclude ".env" \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".pytest_cache" \
  --exclude ".ruff_cache" \
  ./ "${SSH_TARGET}:${VPS_PATH}/"

ssh "${SSH_TARGET}" "cd '${VPS_PATH}' && test -f .env || cp .env.example .env"
ssh "${SSH_TARGET}" "cd '${VPS_PATH}' && docker compose up -d --build"
ssh "${SSH_TARGET}" "cd '${VPS_PATH}' && docker compose ps"
