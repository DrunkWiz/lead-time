# Lead Time on Render (or any container host): build the React app, then serve it
# and the stdlib-only Python API from one process on $PORT.

# 1. Build the frontend
FROM node:22-slim AS web
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# 2. Runtime: Python standard library only, no pip install
FROM python:3.14-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONIOENCODING=utf-8
COPY leadtime/ leadtime/
COPY api/ api/
COPY data/ data/
COPY scripts/dev_server.py scripts/serve.py scripts/precompute.py scripts/
COPY --from=web /web/dist web/dist
# backtest and weekly feeds depend only on the snapshot: compute them here, not per request
RUN python scripts/precompute.py
EXPOSE 8000
CMD ["python", "scripts/serve.py"]
