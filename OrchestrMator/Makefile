setup:
	pip install -r requirements.txt

test:
	pytest

lint:
	ruff check .

run:
	python main.py

docker-up:
	docker compose up -d

docker-down:
	docker compose down
	
db-shell:
	docker exec -it postgres-orchestrmator psql -U orchestrmator_admin -d orchestrmator_db

redis-cli:
	docker exec -it redis-orchestrmator redis-cli

rabbitmq-logs:
	docker logs -f rabbitmq-orchestrmator

minio-logs:
	docker logs -f minio-orchestrmator