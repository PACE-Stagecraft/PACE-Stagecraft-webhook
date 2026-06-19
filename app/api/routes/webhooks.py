import logging

from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import settings
from app.services.github_verifier import verify_signature
from app.services.sqs_publisher import SQSPublisher

logger = logging.getLogger(__name__)

router = APIRouter()

_publisher = SQSPublisher()

@router.post("/github")
async def receive_github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
) -> dict:
    """
    Receive and process GitHub webhook events.

    1. Refuses to process anything if no webhook secret is configured.
    2. Reads the raw body and validates the X-Hub-Signature-256 HMAC.
    3. Forwards every workflow_run event to SQS (queued/in_progress/completed,
       any conclusion) so the unified runs view stays current. Only completed
       failures are flagged with requires_analysis=True for the Bedrock pipeline.
    4. Always returns {"received": true} for accepted events.
    """
    if not settings.GITHUB_WEBHOOK_SECRET:
        logger.error("GITHUB_WEBHOOK_SECRET is not configured; rejecting webhook.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhook receiver is not configured.",
        )

    payload_body = await request.body()

    if not x_hub_signature_256 or not verify_signature(
        payload_body, x_hub_signature_256, settings.GITHUB_WEBHOOK_SECRET
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook signature",
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    if x_github_event != "workflow_run":
        return {"received": True, "published": False}

    run = payload.get("workflow_run", {})
    repo = payload.get("repository", {})
    workflow = payload.get("workflow", {})

    action = payload.get("action")
    run_id = run.get("id")
    repo_owner = repo.get("owner", {}).get("login")
    repo_name = repo.get("name")

    if not isinstance(run_id, int) or not repo_owner or not repo_name:
        logger.warning(
            "Skipping malformed workflow_run payload (run_id=%r, owner=%r, repo=%r)",
            run_id,
            repo_owner,
            repo_name,
        )
        return {"received": True, "published": False}

    requires_analysis = action == "completed" and run.get("conclusion") == "failure"

    sqs_message = {
        "event_type": "workflow_run",
        "action": action,
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "requires_analysis": requires_analysis,
        "run_id": run_id,
        "workflow_id": run.get("workflow_id"),
        "workflow_name": run.get("name"),
        "workflow_file": workflow.get("path", run.get("path", "")),
        "repo_owner": repo_owner,
        "repo_name": repo_name,
        "branch": run.get("head_branch"),
        "head_sha": run.get("head_sha"),
        "started_at": run.get("run_started_at"),
        "completed_at": run.get("updated_at") if action == "completed" else None,
        "html_url": run.get("html_url"),
        "sender_login": payload.get("sender", {}).get("login"),
        "installation_id": payload.get("installation", {}).get("id")
        if payload.get("installation")
        else None,
    }

    await _publisher.publish(sqs_message)
    return {"received": True, "published": True, "requires_analysis": requires_analysis}
