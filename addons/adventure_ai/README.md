# Adventure AI (`adventure_ai`)

Core AdventurePOS AI runtime for Odoo 19 Community.

## Responsibilities

- Provider abstraction (`mock`, `openai`; more later)
- Capability registry (domain modules register typed tools)
- Session / turn ledger and usage metering
- Orchestrator entrypoint (`adventure.ai.orchestrator`)
- Security groups and Settings UI

## Non-responsibilities

- Domain business logic (lives in domain services / `adventure_ai_*` packs)
- Unrestricted ORM access for the LLM
- Hard dependency on Odoo Enterprise AI

## Docs

See [AdventurePOS AI architecture](../../docs/architecture/adventure-ai.md).

## Setup

1. Install this module.
2. **Settings → Adventure AI**: choose provider; set OpenAI key when using `openai`.
3. Grant **Adventure AI / User** to operators who may invoke AI.
4. Install a domain pack (e.g. `adventure_ai_retail`) to register capabilities and UI.
