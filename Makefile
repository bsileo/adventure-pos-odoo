.PHONY: up down logs ps shell-db init-db gcp-vm-start gcp-vm-stop gcp-vm-status gcp-vm-ip remote-dev-init-ssh remote-dev-create remote-dev-start remote-dev-stop remote-dev-status remote-dev-ip remote-dev-url remote-dev-open remote-dev-ssh remote-dev-cursor remote-dev-up remote-dev-init-db remote-dev-bootstrap

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
	bash ./scripts/odoo-init-db.sh

gcp-vm-start:
	gcloud compute instances start $(GCP_INSTANCE) --zone=$(GCP_ZONE) --project=$(GCP_PROJECT)

gcp-vm-stop:
	gcloud compute instances stop $(GCP_INSTANCE) --zone=$(GCP_ZONE) --project=$(GCP_PROJECT)

gcp-vm-status:
	gcloud compute instances describe $(GCP_INSTANCE) --zone=$(GCP_ZONE) --project=$(GCP_PROJECT) --format="value(status)"

gcp-vm-ip:
	gcloud compute instances describe $(GCP_INSTANCE) --zone=$(GCP_ZONE) --project=$(GCP_PROJECT) --format="value(networkInterfaces[0].accessConfigs[0].natIP)"

remote-dev-init-ssh:
	bash ./scripts/remote-dev.sh init-ssh

remote-dev-create:
	bash ./scripts/remote-dev.sh create

remote-dev-start:
	bash ./scripts/remote-dev.sh start

remote-dev-stop:
	bash ./scripts/remote-dev.sh stop

remote-dev-status:
	bash ./scripts/remote-dev.sh status

remote-dev-ip:
	bash ./scripts/remote-dev.sh ip

remote-dev-url:
	bash ./scripts/remote-dev.sh url

remote-dev-open:
	bash ./scripts/remote-dev.sh open

remote-dev-ssh:
	bash ./scripts/remote-dev.sh ssh

remote-dev-cursor:
	bash ./scripts/remote-dev.sh cursor

remote-dev-up:
	bash ./scripts/remote-dev.sh up

remote-dev-init-db:
	bash ./scripts/remote-dev.sh init-db

remote-dev-bootstrap:
	bash ./scripts/remote-dev.sh bootstrap
