# Modernization Roadmap & Implementation Strategy

## PHASE 1: FOUNDATION (Weeks 1-6)

### Goal: Establish modern development infrastructure

#### 1.1 Technology Stack Setup (Week 1-2)
- **Backend Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15 + Redis
- **Message Queue**: RabbitMQ or Kafka
- **Container**: Docker + Docker Compose
- **Version Control**: Git + GitHub/GitLab

**Deliverables**:
- Monorepo structure set up
- Docker Compose for local development
- Basic FastAPI service running
- PostgreSQL schema designed
- CI/CD pipeline skeleton (GitHub Actions)

#### 1.2 Core Data Models (Week 2-3)
```python
# Database Schema
- activities (id, name, domain, description)
- activity_configs (id, activity_id, config_yaml)
- executions (id, cr_id, activity_id, start_time, status)
- node_results (id, execution_id, node_ip, status, data_json)
- parsers (id, name, domain, code, version)
- users (id, email, role)
- audit_logs (id, user_id, action, timestamp)
```

**Deliverables**:
- SQLAlchemy models
- Alembic migrations
- Database seeder with sample data

#### 1.3 API Gateway (Week 3-4)
- REST API endpoints:
  - `POST /api/executions` - Start automation
  - `GET /api/executions/{id}` - Get status
  - `GET /api/activities` - List activities
  - `POST /api/activities` - Create activity
- OpenAPI/Swagger documentation
- JWT authentication
- Request validation (Pydantic)

**Deliverables**:
- FastAPI application
- API documentation
- Postman collection for testing

#### 1.4 Message Queue Integration (Week 4-5)
- RabbitMQ setup
- Task queues: `automation_requests`, `node_executions`
- Celery worker skeleton
- Message producer/consumer

**Deliverables**:
- RabbitMQ running in Docker
- Celery workers can receive tasks
- Basic task execution flow

#### 1.5 CI/CD Pipeline (Week 5-6)
```yaml
# .github/workflows/ci.yml
- Linting (Flake8, Black)
- Type checking (MyPy)
- Unit tests (pytest)
- Build Docker images
- Deploy to dev environment
```

**Deliverables**:
- Automated testing on every commit
- Docker images published to registry
- Dev environment auto-deployed

---

## PHASE 2: CORE MIGRATION (Weeks 7-14)

### Goal: Migrate essential functionality from legacy system

#### 2.1 Activity Configuration Migration (Week 7-8)
- Convert CSV format to YAML/JSON
- Create YAML schema validator
- Migration script: CSV → YAML
- Store in Git repository
- Sync to database on commit

**New Format**:
```yaml
activity:
  name: nokia-syslog-precheck
  domain: pbn
  description: "Nokia syslog configuration verification"

commands:
  - id: 1
    template: "ssh <<<node_user>>>@<<<node_ip>>>"
    parsers: [parse_ssh_login]
    expect_prompt: '[Pp]assword:'
    on_success: 2
    on_failure: 99
```

**Deliverables**:
- 5-10 activities migrated to YAML
- Validator ensuring schema compliance
- Git repository with version history

#### 2.2 Parser Framework Rewrite (Week 8-10)
- Base Parser class
- Dynamic parser loading
- Parser registry
- Parser testing framework

**New Parser Structure**:
```python
from parsers import BaseParser

@register_parser("parse_interface_status")
class InterfaceStatusParser(BaseParser):
    command_pattern = "show interface status"
    
    def parse(self, output: str) -> ParseResult:
        # Parsing logic
        return ParseResult(
            success=True,
            extracted_data={'status': 'up'},
            next_command=None
        )
```

**Deliverables**:
- 20+ parsers migrated
- Parser test suite
- Documentation
