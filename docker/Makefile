# Ref: https://tuic.gov.taipei/documentation/front-end/project-setup

network:
	docker network create --driver=bridge --subnet=192.168.128.0/24 --gateway=192.168.128.1  br_dashboard

db-up:
	docker-compose -f docker-compose-db.yaml up -d

init-up:
	docker-compose -f docker-compose-init.yaml up -d

up:
	docker-compose up -d

down:
	docker-compose down

init-down:
	docker-compose -f docker-compose-init.yaml down

db-down:
	docker-compose -f docker-compose-db.yaml down