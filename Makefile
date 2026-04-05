.PHONY: up down logs ps shell-db

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

shell-db:
	docker compose exec db psql -U odoo -d odoo
