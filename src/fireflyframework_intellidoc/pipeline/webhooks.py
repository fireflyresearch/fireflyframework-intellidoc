# Copyright 2026 Firefly Software Solutions Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Webhook notification service.

Sends HTTP callbacks when processing jobs complete. Webhook
URLs are configured per-job via tags or globally via config.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from pyfly.container.stereotypes import service

from fireflyframework_intellidoc.config import IntelliDocConfig

logger = logging.getLogger(__name__)


@dataclass
class WebhookConfig:
    """Configuration for a webhook endpoint."""

    url: str
    secret: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    retry_count: int = 3
    timeout_seconds: int = 30


@service
class WebhookService:
    """Dispatches webhook callbacks for processing events."""

    def __init__(self, config: IntelliDocConfig) -> None:
        self._config = config

    async def notify_job_completed(
        self,
        job_id: UUID,
        status: str,
        *,
        webhook_url: str | None = None,
        webhook_secret: str = "",
        payload_extras: dict[str, Any] | None = None,
    ) -> bool:
        """Send a webhook notification for a completed job.

        Returns True if the webhook was delivered successfully.
        """
        if not webhook_url:
            return False

        payload = {
            "event": "job.completed",
            "job_id": str(job_id),
            "status": status,
        }
        if payload_extras:
            payload.update(payload_extras)

        return await self._send(
            url=webhook_url,
            payload=payload,
            secret=webhook_secret,
        )

    async def notify_job_failed(
        self,
        job_id: UUID,
        error_message: str,
        *,
        webhook_url: str | None = None,
        webhook_secret: str = "",
    ) -> bool:
        """Send a webhook notification for a failed job."""
        if not webhook_url:
            return False

        payload = {
            "event": "job.failed",
            "job_id": str(job_id),
            "error": error_message,
        }

        return await self._send(
            url=webhook_url,
            payload=payload,
            secret=webhook_secret,
        )

    async def _send(
        self,
        url: str,
        payload: dict[str, Any],
        secret: str = "",
        retries: int = 3,
    ) -> bool:
        """Send a webhook with optional HMAC signature and retries."""
        try:
            import httpx
        except ImportError:
            logger.warning("httpx not installed — webhook delivery skipped")
            return False

        body = json.dumps(payload, default=str)
        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "FireflyIntelliDoc-Webhook/1.0",
        }

        if secret:
            signature = hmac.new(
                secret.encode(), body.encode(), hashlib.sha256
            ).hexdigest()
            headers["X-IntelliDoc-Signature"] = f"sha256={signature}"

        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, content=body, headers=headers)
                    if response.status_code < 300:
                        logger.info(
                            "Webhook delivered to %s (attempt %d)", url, attempt
                        )
                        return True
                    logger.warning(
                        "Webhook to %s returned %d (attempt %d/%d)",
                        url, response.status_code, attempt, retries,
                    )
            except Exception as exc:
                logger.warning(
                    "Webhook to %s failed (attempt %d/%d): %s",
                    url, attempt, retries, exc,
                )

        logger.error("Webhook delivery to %s exhausted all %d retries", url, retries)
        return False
