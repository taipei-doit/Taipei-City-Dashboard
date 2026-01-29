# Ref: https://tuic.gov.taipei/documentation/front-end/project-setup

network:
	docker network create --driver=bridge --subnet=192.168.128.0/24 --gateway=192.168.128.1  br_dashboard
	
up:
	docker-compose -f docker-compose-db.yaml up -d
	docker-compose -f docker-compose-init.yaml up -d
	docker-compose up -d

down:
	docker-compose down
	docker-compose -f docker-compose-init.yaml down
	docker-compose -f docker-compose-db.yaml down -v