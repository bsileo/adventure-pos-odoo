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

## Coding Standards

### Python

* follow Odoo conventions
* small, readable methods
* no unnecessary abstraction

### XML

* clean structure
* minimal XPath complexity
* always comment non-obvious logic

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

Example:

feat(pos): add line item note support

---

## Documentation Rules

Agents must update:

* docs/setup.md → if setup changes
* README.md → if architecture changes
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
