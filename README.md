# agora-webhook

Lightweight FastAPI service that receives GitHub webhook events, verifies HMAC-SHA256 signatures, and publishes to SQS. Kept deliberately separate from the API so it stays always-available regardless of API load.

**Port**: 8001 | **Part of**: [aGora-Ops](https://github.com/aGora-Ops)

## Quick start

```bash
cp .env.example .env
docker compose up --build
# POST /webhooks/github — receives GitHub workflow_run events
```
