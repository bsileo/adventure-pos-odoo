# Adventure POS — Agent Rules & Development Guidelines

## Purpose

This document defines how AI agents (Cursor, OpenClaw, and other tooling) should behave when working in this repository.

The goal is to ensure:

* consistent architecture
* safe code changes
* maintainable Odoo customizations
* predictable development workflows

Agents must follow these rules unless explicitly overridden by a human.

---

## Project Overview

This repository contains a custom Odoo-based system called **Adventure POS**, focused initially on:

* Retail Point of Sale
* Inventory Management
* Customer Management
* Purchasing
* Reporting

This is a **modular Odoo system**, not a monolithic application.

---

## Core Architecture Principles

### 1. Module-First Design

All business logic MUST live in Odoo modules inside:

/addons/

Do NOT:

* modify Odoo core files
* place logic outside modules
* duplicate logic across modules

---

### 2. Current Module Scope

Initial modules:

* adventure_base
* adventure_pos
* adventure_inventory
* adventure_customers
* adventure_purchase
* adventure_reports

Future modules (do not implement unless instructed):

* adventure_rental
* adventure_service
* adventure_loyalty
* adventure_training
* adventure_trips
* adventure_multi_store

---

### 3. Safe Extension Rules

Agents MUST:

* use model inheritance (_inherit)
* use extension patterns, not overrides when possible
* preserve upgrade compatibility

Avoid:

* monkey patching
* deleting core behavior
* fragile XPath expressions in XML

---

### 4. Configuration as code (mandatory for agreed Odoo settings)

When the team **decides** on an Odoo configuration that must exist in **test, staging, production, or every new developer database** (Settings screens, system parameters, required master data, POS shop defaults, etc.), that outcome MUST be **captured in the repository**, not left only as manual changes in one database.

Agents and developers MUST implement repeatability using one or more of:

* **Module data files** (`data/` XML or CSV, with appropriate `noupdate` flags) in the right `adventure_*` module—or a dedicated thin setup module if the team adds one (e.g. `adventure_setup`).
* **`post_init_hook` / `pre_init_hook`** in the manifest when hooks are the right tool.
* **Documented deployment scripts** (e.g. Odoo shell or API calls) checked into `scripts/` or `docs/`, if something cannot be expressed cleanly in XML.

Agents MUST NOT treat “we configured it in the UI on my laptop” as done unless the same result is encoded for the next install/upgrade.

**Acceptable exceptions** (must still be followed up):

* Short **spikes** or demos—then either discard the DB or **promote** the final decisions into module data or scripts before merge to shared branches.
* **Emergency production** tweaks—document and **backport** into the repo in the same change train.

Pull requests that introduce or rely on **team-mandatory** configuration without a repeatable artifact in git should be flagged; humans may allow a time-boxed follow-up task, but the default expectation is **script or data file in the same PR** when the change is agreed.

---

## Coding Standards

### Python

* follow Odoo conventions
* small, readable methods
* no unnecessary abstraction

### XML

* clean structure
* minimal XPath complexity
* always comment non-obvious logic

### Module install / upgrade (local dev)

After **Python model changes** (new fields, field definitions, or other schema-related model code) or **data/XML** that the module must load into the database, the affected module must be **upgraded** so the ORM and database stay in sync.

* **Restarting Odoo only** does not add columns or apply module data; skipping an upgrade can surface as HTTP 500 with `UndefinedColumn` (or similar) when SQL selects fields the database never received.
* Tell the human (or note in the PR) to **upgrade the module**: for example **Apps** → show installed modules → open the module → **Upgrade**, or from Docker: `odoo -d <database> -u <module> --stop-after-init` (then start the service as usual).
* Bump **`version` in `__manifest__.py`** when a change requires an upgrade so environments can spot drift; use patch bumps for small additive changes unless the team prefers otherwise.

### Naming

Use consistent prefixes:

adventure_*

Examples:

* adventure_pos
* adventure_inventory

---

## Data & Security Rules

Agents MUST NOT:

* change access rules without explanation
* expose sensitive data
* remove security constraints

All changes to:

* ir.model.access
* record rules

Require explanation in PR.

---

## POS-Specific Rules

When modifying POS:

* preserve checkout speed
* avoid unnecessary UI friction
* never break barcode flow
* ensure offline compatibility where possible

---

## Inventory Rules

* never break stock valuation logic
* preserve product variants integrity
* do not modify core stock moves unless necessary

---

## Agent Behavior Rules

### Always Do

* explain major changes before applying
* make small, incremental edits
* keep commits focused
* update documentation when needed

### Never Do

* large refactors without approval
* delete modules or directories
* introduce breaking schema changes silently
* commit secrets or credentials

---

## Git Workflow

* work on feature branches only
* never commit directly to main
* use descriptive commit messages
* link PRs to GitHub Issues (`Closes #123`) when an issue exists — see [development-tracking.md](development-tracking.md)

Example:

feat(pos): add line item note support

---

## Documentation Rules

Agents must update:

* docs/setup.md → if setup changes
* README.md → if architecture changes
* docs/development-tracking.md → if GitHub Issues / PR workflow for humans changes
* module README if logic becomes complex

---

## OpenAI / OpenClaw Usage

* never store API keys in code
* use environment variables only
* assume local-only execution unless specified

---

## When Unsure

Agents should:

1. Ask for clarification
2. Propose options
3. Avoid making assumptions

---

## Guiding Principle

Build a **clean, scalable retail POS system first**.

Do NOT prematurely build:

* rentals
* service systems
* complex multi-location features

Focus on:

**POS + Inventory + Customers working extremely well**

---
