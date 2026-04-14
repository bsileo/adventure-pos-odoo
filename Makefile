.PHONY: up down logs ps shell-db init-db gcp-vm-start gcp-vm-stop gcp-vm-status gcp-vm-ip

# Shared GCP sandbox VM (override per developer if needed: make gcp-vm-stop GCP_ZONE=us-east1-b)
GCP_PROJECT ?= adventure-pos-sandbox
GCP_ZONE ?= us-central1-a
GCP_INSTANCE ?= adventurepos-sandbox-vm

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

gcp-vm-start:
	gcloud compute instances start $(GCP_INSTANCE) --zone=$(GCP_ZONE) --project=$(GCP_PROJECT)

gcp-vm-stop:
	gcloud compute instances stop $(GCP_INSTANCE) --zone=$(GCP_ZONE) --project=$(GCP_PROJECT)

gcp-vm-status:
	gcloud compute instances describe $(GCP_INSTANCE) --zone=$(GCP_ZONE) --project=$(GCP_PROJECT) --format="value(status)"

gcp-vm-ip:
	gcloud compute instances describe $(GCP_INSTANCE) --zone=$(GCP_ZONE) --project=$(GCP_PROJECT) --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
