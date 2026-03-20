FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/portal-mcp

COPY dataagent/portal-mcp/requirements.txt /tmp/requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r /tmp/requirements.txt

COPY dataagent/portal-mcp /app/portal-mcp

EXPOSE 8801

CMD ["uvicorn", "portal_mcp.app:app", "--host", "0.0.0.0", "--port", "8801"]
