# Adventure AI Retail (`adventure_ai_retail`)

Retail domain pack for AdventurePOS AI.

## Capabilities

- `search_products` — read-only product search via `adventure.product_search`

## POS

Adds an **AI** button on the POS navbar that opens a natural-language search panel. Results are added with normal POS `addLineToCurrentOrder` APIs (no LLM writes).

## Docs

[AdventurePOS AI architecture](../../docs/architecture/adventure-ai.md)
