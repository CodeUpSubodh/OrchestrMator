setup:
	pip install -r requirements.txt

test:
	pytest

lint:
	ruff check .

# Run UNIFIED application (all services mounted together)
run:
	uvicorn backend.main:app --reload --port 8000

# Run ONLY API Gateway (isolated)
run-api:
	uvicorn backend.api_gateway.main:app --reload --port 8000

# Run ONLY Celery Worker (isolated) - Phase 3
run-worker:
	celery -A backend.workflow_engine.celery_app worker --loglevel=info

# Run ONLY Celery Beat (isolated) - Phase 3
run-beat:
	celery -A backend.workflow_engine.celery_app beat --loglevel=info

# Run all services in production mode (requires separate terminals)
run-all:
	@echo "Run these commands in separate terminals:"
	@echo "  make run-api      # Port 8000"
	@echo "  make run-worker   # Celery worker"
	@echo "  make run-beat     # Celery scheduler"

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