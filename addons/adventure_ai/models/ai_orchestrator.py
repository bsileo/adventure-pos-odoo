# -*- coding: utf-8 -*-

import json
import logging
import time
from typing import Any, Dict, List, Optional

from odoo import _, api, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.adventure_ai.providers.mock_provider import MockProvider
from odoo.addons.adventure_ai.providers.openai_provider import OpenAIProvider
from odoo.addons.adventure_ai.services import capability_registry as caps

_logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 3

PROFILE_SYSTEM_PROMPTS = {
    "pos_retail": (
        "You are the AdventurePOS retail assistant for a point-of-sale cashier. "
        "Use only the provided tools. Prefer search_products for product lookup. "
        "Do not invent products, prices, or stock. Keep assistant text brief."
    ),
    "default": (
        "You are an AdventurePOS assistant. Use only the provided tools. "
        "Do not invent business data. Prefer tools over guessing."
    ),
}


class AdventureAiOrchestrator(models.AbstractModel):
    _name = "adventure.ai.orchestrator"
    _description = "Adventure AI Orchestrator"

    def _ensure_ai_user(self):
        if not self.env.user.has_group("adventure_ai.group_user"):
            raise AccessError(_("You need Adventure AI User rights to use AI features."))

    def _get_provider(self):
        provider_name = (
            self.env["ir.config_parameter"].sudo().get_param("adventure_ai.provider") or "mock"
        ).strip()
        if provider_name == "openai":
            return OpenAIProvider(self.env)
        if provider_name == "mock":
            return MockProvider(self.env)
        raise UserError(_("Unsupported AI provider: %s") % provider_name)

    def _system_prompt(self, profile: str) -> str:
        return PROFILE_SYSTEM_PROMPTS.get(profile) or PROFILE_SYSTEM_PROMPTS["default"]

    def _next_sequence(self, session) -> int:
        return (max(session.turn_ids.mapped("sequence") or [0]) + 10)

    def _log_usage(
        self,
        session,
        *,
        feature: str,
        capability_name: Optional[str],
        provider_result,
        latency_ms: int,
        success: bool,
        error_message: str = "",
    ):
        provider = self._get_provider()
        estimated = provider.estimate_cost(
            provider_result.input_tokens if provider_result else 0,
            provider_result.output_tokens if provider_result else 0,
            (provider_result.model if provider_result else "") or "mock",
        )
        self.env["adventure.ai.usage"].sudo().create(
            {
                "session_id": session.id,
                "user_id": self.env.user.id,
                "feature": feature or "general",
                "capability_name": capability_name or False,
                "provider": (provider_result.provider if provider_result else provider.name),
                "model": (provider_result.model if provider_result else False),
                "channel": session.channel,
                "profile": session.profile,
                "input_tokens": provider_result.input_tokens if provider_result else 0,
                "output_tokens": provider_result.output_tokens if provider_result else 0,
                "estimated_cost": estimated,
                "latency_ms": latency_ms,
                "success": success,
                "error_message": error_message or False,
                "company_id": self.env.company.id,
            }
        )

    @api.model
    def get_or_create_session(self, session_id=None, profile="default", channel="backend"):
        self._ensure_ai_user()
        Session = self.env["adventure.ai.session"].sudo()
        if session_id:
            session = Session.browse(int(session_id)).exists()
            if session:
                if session.user_id != self.env.user and not self.env.user.has_group(
                    "adventure_ai.group_manager"
                ):
                    raise AccessError(_("You cannot continue another user's AI session."))
                return session
        return Session.create(
            {
                "name": _("AI (%s)") % profile,
                "profile": profile or "default",
                "channel": channel or "backend",
                "user_id": self.env.user.id,
            }
        )

    @api.model
    def run_turn(self, message, session_id=None, profile="pos_retail", channel="pos", context=None):
        """Run one user turn: provider completion + constrained tool loop.

        :return: dict suitable for POS/backend Owl clients
        """
        self._ensure_ai_user()
        message = (message or "").strip()
        if not message:
            raise UserError(_("Enter a message for the AI assistant."))

        context = dict(context or {})
        session = self.get_or_create_session(
            session_id=session_id, profile=profile, channel=channel
        )
        if session.state != "open":
            raise UserError(_("This AI session is closed."))

        started = time.monotonic()
        provider = self._get_provider()
        tools = caps.tools_for_provider(session.profile)
        feature = context.get("feature") or (
            "pos_retail" if session.profile == "pos_retail" else session.profile or "general"
        )

        seq = self._next_sequence(session)
        self.env["adventure.ai.turn"].sudo().create(
            {
                "session_id": session.id,
                "sequence": seq,
                "role": "user",
                "content": message,
            }
        )

        messages = [
            {"role": "system", "content": self._system_prompt(session.profile)}
        ]
        for turn in session.turn_ids.sorted(key=lambda t: (t.sequence, t.id)):
            if turn.role == "tool":
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": turn.tool_call_id or "",
                        "content": turn.content or "",
                    }
                )
            else:
                messages.append({"role": turn.role, "content": turn.content or ""})

        tool_results: List[Dict[str, Any]] = []
        assistant_text = ""
        provider_result = None
        last_capability = None

        try:
            for _iteration in range(MAX_TOOL_ITERATIONS):
                provider_result = provider.complete(messages, tools=tools or None)
                if provider_result.tool_calls:
                    assistant_payload = {
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "name": tc.name,
                                "arguments": tc.arguments,
                            }
                            for tc in provider_result.tool_calls
                        ]
                    }
                    seq = self._next_sequence(session)
                    self.env["adventure.ai.turn"].sudo().create(
                        {
                            "session_id": session.id,
                            "sequence": seq,
                            "role": "assistant",
                            "content": provider_result.content or "",
                            "payload_json": assistant_payload,
                        }
                    )
                    messages.append(
                        {
                            "role": "assistant",
                            "content": provider_result.content or None,
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.name,
                                        "arguments": json.dumps(tc.arguments),
                                    },
                                }
                                for tc in provider_result.tool_calls
                            ],
                        }
                    )
                    for tc in provider_result.tool_calls:
                        last_capability = tc.name
                        result = caps.invoke_capability(
                            self.env,
                            tc.name,
                            tc.arguments,
                            context={**context, "session_id": session.id, "channel": channel},
                        )
                        serialized = self._serialize_tool_result(result)
                        tool_results.append(
                            {
                                "tool_call_id": tc.id,
                                "name": tc.name,
                                "arguments": tc.arguments,
                                "result": serialized,
                            }
                        )
                        seq = self._next_sequence(session)
                        tool_content = json.dumps(serialized, default=str)
                        self.env["adventure.ai.turn"].sudo().create(
                            {
                                "session_id": session.id,
                                "sequence": seq,
                                "role": "tool",
                                "tool_name": tc.name,
                                "tool_call_id": tc.id,
                                "content": tool_content,
                                "payload_json": serialized,
                            }
                        )
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "content": tool_content,
                            }
                        )
                    # After tools run, stop for Phase 1 (POS renders structured results).
                    # Avoid a second paid completion solely for prose summaries.
                    if tool_results:
                        count = len(self._extract_products(tool_results))
                        assistant_text = _(
                            "Found %(count)s product(s). Select an item to add it to the order."
                        ) % {"count": count}
                        seq = self._next_sequence(session)
                        self.env["adventure.ai.turn"].sudo().create(
                            {
                                "session_id": session.id,
                                "sequence": seq,
                                "role": "assistant",
                                "content": assistant_text,
                            }
                        )
                        break
                    continue

                assistant_text = provider_result.content or ""
                seq = self._next_sequence(session)
                self.env["adventure.ai.turn"].sudo().create(
                    {
                        "session_id": session.id,
                        "sequence": seq,
                        "role": "assistant",
                        "content": assistant_text,
                    }
                )
                break
            else:
                assistant_text = assistant_text or _(
                    "I found results using tools; ask if you need a shorter summary."
                )

            latency_ms = int((time.monotonic() - started) * 1000)
            self._log_usage(
                session,
                feature=feature,
                capability_name=last_capability,
                provider_result=provider_result,
                latency_ms=latency_ms,
                success=True,
            )
            session.last_error = False
            return {
                "session_id": session.id,
                "assistant_text": assistant_text,
                "tool_results": tool_results,
                "products": self._extract_products(tool_results),
                "provider": provider_result.provider if provider_result else provider.name,
                "model": provider_result.model if provider_result else "",
                "latency_ms": latency_ms,
            }
        except Exception as exc:
            latency_ms = int((time.monotonic() - started) * 1000)
            _logger.exception("AI orchestrator turn failed")
            self._log_usage(
                session,
                feature=feature,
                capability_name=last_capability,
                provider_result=provider_result,
                latency_ms=latency_ms,
                success=False,
                error_message=str(exc),
            )
            session.last_error = str(exc)
            raise

    def _serialize_tool_result(self, result: Any) -> Any:
        if result is None:
            return None
        if isinstance(result, (dict, list, str, int, float, bool)):
            return result
        if hasattr(result, "read"):
            return result.read()
        return str(result)

    def _extract_products(self, tool_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        products: List[Dict[str, Any]] = []
        for item in tool_results:
            if item.get("name") != "search_products":
                continue
            result = item.get("result") or {}
            hits = result.get("products") if isinstance(result, dict) else None
            if isinstance(hits, list):
                products.extend(hits)
        return products
