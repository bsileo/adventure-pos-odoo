# -*- coding: utf-8 -*-
"""OpenAI-compatible chat completions provider (HTTPS, no SDK dependency)."""

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from odoo.exceptions import UserError

from .base import BaseProvider, ProviderResult, ToolCall
from .mock_provider import parse_tool_arguments

_logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    name = "openai"

    def complete(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ProviderResult:
        ICP = self.env["ir.config_parameter"].sudo()
        api_key = (ICP.get_param("adventure_ai.openai_api_key") or "").strip()
        if not api_key:
            raise UserError(
                "OpenAI API key is not configured. Set it under Settings → Adventure AI, "
                "or switch the provider to Mock."
            )
        model = (
            kwargs.get("model")
            or ICP.get_param("adventure_ai.openai_model")
            or "gpt-4o-mini"
        )
        base_url = (
            ICP.get_param("adventure_ai.openai_base_url") or "https://api.openai.com/v1"
        ).rstrip("/")
        url = "%s/chat/completions" % base_url

        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = kwargs.get("tool_choice", "auto")

        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={
                "Authorization": "Bearer %s" % api_key,
                "Content-Type": "application/json",
                "User-Agent": "AdventurePOS-adventure_ai/1.0",
            },
        )
        timeout = float(ICP.get_param("adventure_ai.http_timeout") or 45)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw_body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            _logger.warning("OpenAI HTTP error %s: %s", exc.code, detail)
            raise UserError("OpenAI request failed (%s): %s" % (exc.code, detail[:500])) from exc
        except urllib.error.URLError as exc:
            _logger.warning("OpenAI connection error: %s", exc)
            raise UserError("Could not reach OpenAI: %s" % exc.reason) from exc

        data = json.loads(raw_body)
        choice = (data.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        usage = data.get("usage") or {}
        tool_calls = []
        for item in message.get("tool_calls") or []:
            function = item.get("function") or {}
            try:
                arguments = parse_tool_arguments(function.get("arguments"))
            except json.JSONDecodeError as exc:
                raise UserError(
                    "Model returned invalid tool arguments for %s." % function.get("name")
                ) from exc
            tool_calls.append(
                ToolCall(
                    id=item.get("id") or "",
                    name=function.get("name") or "",
                    arguments=arguments,
                )
            )
        return ProviderResult(
            content=message.get("content") or "",
            tool_calls=tool_calls,
            provider=self.name,
            model=data.get("model") or model,
            input_tokens=int(usage.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("completion_tokens") or 0),
            raw=data,
        )
