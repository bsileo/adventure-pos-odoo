# -*- coding: utf-8 -*-
"""Thin Smartwaiver REST client (API v4).

Secrets are never logged. Callers pass the API key explicitly.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

_logger = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.smartwaiver.com"
DEFAULT_TIMEOUT = 60


class SmartwaiverAPIError(Exception):
    """Raised when Smartwaiver returns an HTTP or payload error."""

    def __init__(self, message, status_code=None, payload=None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class SmartwaiverClient:
    def __init__(self, api_key, base_url=None, timeout=DEFAULT_TIMEOUT):
        if not api_key:
            raise SmartwaiverAPIError("Smartwaiver API key is not configured.")
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _request(self, method, path, query=None, body=None):
        url = f"{self.base_url}{path}"
        if query:
            filtered = {k: v for k, v in query.items() if v is not None and v != ""}
            if filtered:
                url = f"{url}?{urllib.parse.urlencode(filtered)}"
        data = None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            payload = None
            try:
                payload = json.loads(exc.read().decode("utf-8"))
                message = payload.get("message") or str(exc)
            except Exception:  # noqa: BLE001 — best-effort parse
                message = str(exc)
            _logger.warning(
                "Smartwaiver HTTP %s on %s %s: %s",
                exc.code,
                method,
                path,
                message,
            )
            raise SmartwaiverAPIError(message, status_code=exc.code, payload=payload) from exc
        except urllib.error.URLError as exc:
            raise SmartwaiverAPIError(f"Smartwaiver connection error: {exc.reason}") from exc

    def get_waiver_summaries(
        self,
        limit=20,
        verified=None,
        template_id=None,
        from_dts=None,
        to_dts=None,
    ):
        query = {
            "limit": limit,
            "templateId": template_id or "",
            "fromDts": from_dts or "",
            "toDts": to_dts or "",
        }
        if verified is not None:
            query["verified"] = "true" if verified else "false"
        payload = self._request("GET", "/v4/waivers", query=query)
        return payload.get("waivers") or []

    def get_waiver(self, waiver_id, pdf=False):
        payload = self._request(
            "GET",
            f"/v4/waivers/{urllib.parse.quote(str(waiver_id))}",
            query={"pdf": "true" if pdf else "false"},
        )
        return payload.get("waiver") or payload

    def get_templates(self):
        payload = self._request("GET", "/v4/templates")
        return payload.get("templates") or []

    def search(
        self,
        template_id=None,
        from_dts=None,
        to_dts=None,
        first_name=None,
        last_name=None,
        verified=None,
        email=None,
        tag=None,
        sort_descending=True,
    ):
        query = {
            "templateId": template_id or "",
            "fromDts": from_dts or "",
            "toDts": to_dts or "",
            "firstName": first_name or "",
            "lastName": last_name or "",
            "email": email or "",
            "tag": tag or "",
            "sort": "desc" if sort_descending else "asc",
        }
        if verified is not None:
            query["verified"] = "true" if verified else "false"
        payload = self._request("GET", "/v4/search", query=query)
        search = payload.get("search") or payload
        return search.get("guid") or search.get("searchGUID")

    def search_results(self, guid, page=0, pdf=False):
        payload = self._request(
            "GET",
            f"/v4/search/{urllib.parse.quote(str(guid))}/results",
            query={"page": page, "pdf": "true" if pdf else "false"},
        )
        return payload.get("search_results") or []

    def get_webhook_config(self):
        payload = self._request("GET", "/v4/webhooks/configure")
        return payload.get("webhooks") or payload.get("webhook") or payload

    def get_webhook_queues(self):
        payload = self._request("GET", "/v4/webhooks/queues")
        return payload.get("webhooks") or payload

    def get_webhook_queue_account_message(self, delete=False):
        """Retrieve one account-queue webhook message (new-waiver notifications).

        Prefer delete=False, process the waiver, then call
        delete_webhook_queue_account_message so a processing failure does not
        drop the queue item.
        """
        payload = self._request(
            "GET",
            "/v4/webhooks/queues/account",
            query={"delete": "true" if delete else "false"},
        )
        # Empty queue responses vary; normalize to None when no message.
        message = payload.get("message") or payload.get("webhook")
        if message:
            return message
        if payload.get("messageId") or payload.get("payload"):
            return payload
        return None

    def delete_webhook_queue_account_message(self, message_id):
        return self._request(
            "DELETE",
            f"/v4/webhooks/queues/account/{urllib.parse.quote(str(message_id))}",
        )
