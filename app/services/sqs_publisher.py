import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import boto3

from app.core.config import settings

_executor = ThreadPoolExecutor(max_workers=4)

class SQSPublisher:
    """Publishes messages to an AWS SQS queue using boto3."""

    def __init__(self) -> None:
        self._client = boto3.client("sqs", region_name=settings.AWS_REGION)

    async def publish(self, message: dict[str, Any]) -> str:
        """
        Serialize and publish a message to SQS.

        Runs the blocking boto3 call in a thread pool executor to avoid
        blocking the async event loop.

        Returns:
            The SQS MessageId of the published message.
        """
        loop = asyncio.get_event_loop()
        message_body = json.dumps(message)
        response = await loop.run_in_executor(
            _executor,
            lambda: self._client.send_message(
                QueueUrl=settings.SQS_QUEUE_URL,
                MessageBody=message_body,
            ),
        )
        return response["MessageId"]
