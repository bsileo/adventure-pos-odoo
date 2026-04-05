# Adventure POS — Initial Setup Guide

> **Cloning the repo?** Use [developer-onboarding.md](developer-onboarding.md) for step-by-step directions. This page is the original greenfield/bootstrap checklist.

This guide walks through setting up the local development environment using:

* Cursor (IDE + agent)
* Docker (Odoo + Postgres)
* GitHub (repo)
* OpenClaw (local assistant)
* OpenAI API (model provider)

---

## Step 1 — Create Project Folder

Open Cursor and:

* Create a new empty folder:

  adventure-pos-odoo

* Open it in Cursor

---

## Step 2 — Initialize Git Repository

Open terminal inside Cursor:

git init

Create initial structure:

mkdir addons
mkdir config
mkdir docs
mkdir scripts

---

## Step 3 — Create Core Files

Create these files:

README.md
.env.example
docker-compose.yml
Makefile

---

## Step 4 — Create .env File

Create:

.env

Add:

OPENAI_API_KEY=
ODOO_VERSION=18.0
POSTGRES_DB=odoo
POSTGRES_USER=odoo
POSTGRES_PASSWORD=change_me_local_dev
ODOO_PORT=8069

---

## Step 5 — Docker Setup

Create:

docker-compose.yml

Paste (credentials come from `.env`; see `.env.example`):

services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-odoo}
      POSTGRES_USER: ${POSTGRES_USER:-odoo}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env (see .env.example)}
    ports:
      - "5432:5432"

  odoo:
    image: odoo:18.0
    depends_on:
      - db
    environment:
      HOST: db
      USER: ${POSTGRES_USER:-odoo}
      PASSWORD: ${POSTGRES_PASSWORD:?Set POSTGRES_PASSWORD in .env (see .env.example)}
    ports:
      - "8069:8069"
    volumes:
      - ./addons:/mnt/extra-addons

---

## Step 6 — Start Odoo

Run:

docker compose up -d

Then open:

http://localhost:8069

Create your first database.

---

## Step 7 — Create First Module

Inside addons:

adventure_base

Structure:

addons/adventure_base/
**init**.py
**manifest**.py
models/

Basic manifest:

{
"name": "Adventure Base",
"version": "1.0",
"depends": ["base"],
"data": [],
"installable": True
}

---

## Step 8 — Setup Cursor Rules

Create folder:

.cursor/rules/

Add:

odoo.mdc
repo.mdc

Then copy rules from:

docs/agent-rules.md

---

## Step 9 — Setup OpenAI Key

Set environment variable:

Mac/Linux:
export OPENAI_API_KEY="your_key"

Windows:
setx OPENAI_API_KEY "your_key"

---

## Step 10 — Install OpenClaw

Install OpenClaw locally.

Create config:

config/openclaw.json5

Basic example:

{
"models": {
"default": {
"provider": "openai",
"model": "gpt-5.4"
}
}
}

Run OpenClaw and confirm it connects.

---

## Step 11 — Connect to GitHub

Create repo on GitHub:

adventure-pos-odoo

Then:

git add .
git commit -m "initial setup"
git branch -M main
git remote add origin <repo-url>
git push -u origin main

---

## Step 12 — Create Development Branch

git checkout -b develop
git push -u origin develop

---

## Step 13 — Verify System

You should now have:

* Odoo running locally
* Git repo initialized
* Cursor configured
* OpenClaw connected
* OpenAI working

---

## Next Steps

1. Build adventure_pos module
2. Add inventory enhancements
3. Define POS workflow improvements
4. Add basic reporting

---

## Notes

* Do NOT store secrets in repo
* Do NOT modify Odoo core
* Keep all logic in /addons

---

## Goal

At the end of setup, you should be able to:

* run Odoo locally
* build custom modules
* use Cursor agents safely
* use OpenClaw for assistance
* push changes to GitHub

---
