.PHONY: up down logs ps shell-db init-db

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

# Initialize Postgres DB named `odoo` with Odoo core (required once after first `up` if you get HTTP 500 on /).
init-db:
	docker compose exec odoo odoo --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo -d odoo -i base --stop-after-init
