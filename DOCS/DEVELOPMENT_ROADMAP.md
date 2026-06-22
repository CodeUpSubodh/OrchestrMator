# OrchestrMator - Development Roadmap

## Overview

This document provides a **complete step-by-step guide** to build OrchestrMator from scratch. Each phase builds on the previous one and produces working software.

**Total Timeline**: 27 weeks (6-7 months)  
**Team Size**: 2-3 developers recommended

---

## Prerequisites

Before starting development:

✅ Python 3.11+ installed  
✅ Docker & Docker Compose installed  
✅ Git installed  
✅ PostgreSQL client (psql) installed  
✅ Code editor (VS Code recommended)  
✅ Basic knowledge of: Python, FastAPI, SQL, Docker, React (for frontend)

---

## Phase 0: Project Setup (Week 0 - 3 days)

### Goal
Set up development environment and project structure.

### Tasks

**0.1 Initialize Project**
- Create GitHub/GitLab repository
- Clone repository locally
- Create project folder structure:
  ```
  OrchestrMator/
  ├── backend/
  ├── frontend/
  ├── infrastructure/
  ├── tests/
  ├── docs/
  └── config-repository/
  ```
- Initialize Git with `.gitignore`

**0.2 Create Docker Compose Setup**
- Create `docker-compose.yml` with:
  - PostgreSQL 15
  - Redis 7
  - RabbitMQ 3.12 (with management UI)
  - MinIO (S3-compatible)
- Create `.env.example` with all required environment variables
- Test: `docker-compose up` should start all services

**0.3 Python Environment Setup**
- Create `requirements.txt` with core dependencies:
  - fastapi
  - uvicorn[standard]
  - sqlalchemy
  - psycopg2-binary
  - alembic
  - celery
  - redis
  - pydantic
  - python-jose[cryptography]
  - passlib[bcrypt]
  - paramiko
  - pytest
  - pytest-cov
  - hypothesis
- Create virtual environment: `python3.11 -m venv venv`
- Install dependencies: `pip install -r requirements.txt`

**0.4 Create Makefile**
- Add common commands: setup, test, lint, run, docker-up, docker-down
- Test all make commands work

**0.5 Create README.md**
- Project description
- Setup instructions
- Architecture overview
- Contribution guidelines

**Checkpoint**: Can you run `docker-compose up` and `make test` successfully?

---

## Phase 1: Database Foundation (Week 1-2)

### Goal
Set up database models, migrations, and basic CRUD operations.

### Tasks

**1.1 Configure SQLAlchemy**
- Create `backend/shared/database.py`
  - Database connection with connection pooling
  - Session factory
  - Base class for models
  - `get_db()` dependency for FastAPI
- Create `backend/shared/config.py`
  - Pydantic settings for configuration
  - Load from environment variables
  - Database URL construction

**1.2 Initialize Alembic**
- Run `alembic init alembic`
- Configure `alembic.ini` with database URL
- Update `alembic/env.py` to use Base metadata
- Create initial migration: `alembic revision --autogenerate -m "initial"`

**1.3 Create Database Models**

Create `backend/shared/models.py` with:

- **User Model**
  - id, email, password_hash, role, is_active
  - timestamps (created_at, updated_at)
  - Methods: `verify_password()`, `set_password()`

- **Activity Model**
  - id, name, domain, description, config (JSONB)
  - version, git_commit_sha, is_active
  - Relationship: belongs to User (created_by)

- **Execution Model**
  - id, user_id, activity_id, cr_id, status
  - execution_mode, input_data (JSONB), max_parallelism
  - timestamps, trigger_source, trigger_metadata
  - Relationships: belongs to User, belongs to Activity, has many NodeResults

- **NodeResult Model**
  - id, execution_id, node_name, node_ip, status
  - extracted_data (JSONB), state_data (JSONB)
  - log_file_path, error_message
  - execution_priority, batch_id
  - Relationship: belongs to Execution, has many CommandResults

- **CommandResult Model**
  - id, node_result_id, command_id, command_text
  - output (TEXT), parsed_output (JSONB), status
  - parser_used, execution_time_ms
  - Relationship: belongs to NodeResult

- **Parser Model**
  - id, name, domain, parser_type, code (TEXT)
  - config (JSONB), description, is_active
  - Relationship: belongs to User (created_by)

- **Schedule Model**
  - id, activity_id, user_id, cron_expression
  - one_time_execution_at, input_data (JSONB)
  - next_execution_at, is_recurring, active

- **AuditLog Model**
  - id, user_id, action, resource_type, resource_id
  - ip_address, user_agent, success, details (JSONB)
  - timestamp

**1.4 Run Migrations**
- Generate migration: `alembic revision --autogenerate -m "create all tables"`
- Review generated migration file
- Apply migration: `alembic upgrade head`
- Verify: `psql` to check tables created

**1.5 Create Pydantic Schemas**

Create `backend/shared/schemas.py` with:

- Request/Response schemas for each model
- Validation logic
- Example: `ActivityCreate`, `ActivityResponse`, `ExecutionCreateRequest`

**1.6 Write Unit Tests**

Create `tests/unit/test_models.py`:
- Test model creation
- Test JSONB fields
- Test relationships
- Test constraints

**Checkpoint**: Can you create a User and Activity in the database using SQLAlchemy?

---

## Phase 2: Core API Gateway (Week 3)

### Goal
Create FastAPI application with authentication and basic CRUD endpoints.

### 📋 DETAILED SPECIFICATION
**For complete API contracts, request/response formats, business logic, and implementation guidelines, see:**
**[PHASE_2_API_GATEWAY_DETAILED.md](./PHASE_2_API_GATEWAY_DETAILED.md)**

This detailed document includes:
- Full request/response JSON examples for every endpoint
- Business logic and validation rules
- Error handling specifications
- Implementation code snippets
- Complete integration test suite
- Tips for working with AI coding assistants

### Tasks Summary

**2.1 Create FastAPI Application**

Create `backend/api_gateway/main.py`:
- Initialize FastAPI app with title, description, version
- Configure CORS middleware (allow frontend origin)
- Add exception handlers (RequestValidationError, etc.)
- Add logging configuration
- Configure OpenAPI docs at /api/docs

**2.2 Implement Authentication (4 Endpoints)**

Create `backend/api_gateway/auth.py`:
- JWT token creation/validation functions
- Password hashing utilities
- OAuth2 password flow configuration
- `get_current_user()` dependency function

Create endpoints in `backend/api_gateway/routes/auth.py`:
- `POST /api/v1/auth/register` - Register new user (validate email, hash password)
- `POST /api/v1/auth/login` - Login and get JWT tokens (access + refresh)
- `POST /api/v1/auth/refresh` - Refresh access token using refresh token
- `GET /api/v1/auth/me` - Get current authenticated user info

**2.3 Implement Activity CRUD (5 Endpoints)**

Create `backend/api_gateway/routes/activities.py`:
- `GET /api/v1/activities` - List activities (paginated, filter by domain/status/search/creator)
- `POST /api/v1/activities` - Create activity (validate config structure)
- `GET /api/v1/activities/{id}` - Get activity details
- `PUT /api/v1/activities/{id}` - Update activity (check permissions)
- `DELETE /api/v1/activities/{id}` - Soft-delete activity (set is_active=false)

**Config Validation:** Ensure config has `commands` array, `authentication` object, and `state_data_map`.

**2.4 Implement Execution Endpoints (5 Endpoints)**

Create `backend/api_gateway/routes/executions.py`:
- `POST /api/v1/executions` - Start execution (validate input_data with nodes array, set status=queued)
- `GET /api/v1/executions` - List executions (filter by activity/status/CR ID/date range)
- `GET /api/v1/executions/{id}` - Get execution details with statistics
- `GET /api/v1/executions/{id}/results` - Get node results with optional command details
- `DELETE /api/v1/executions/{id}` - Cancel execution (only if queued or running)

**Input Validation:** Each node must have `node_name` and `node_ip`. Validate IP format.

**2.5 Add Health Check (3 Endpoints)**

Create `backend/api_gateway/routes/health.py`:
- `GET /health` - Basic health check (always 200 if running)
- `GET /health/ready` - Readiness check (test DB/Redis/RabbitMQ connections)
- `GET /health/live` - Liveness check (for Kubernetes pod restart logic)

**2.6 Write Integration Tests**

Create `tests/integration/test_api.py`:
- Test authentication flow (register → login → get user)
- Test duplicate email registration (409 error)
- Test wrong password login (401 error)
- Test activity CRUD operations (create → get → update → list → delete)
- Test execution creation and listing
- Test unauthorized access (401 without token)
- Test invalid token (401 with bad token)
- Test permission checks (403 when updating others' activities)

**Use pytest with TestClient and SQLite in-memory database for isolated tests.**

**Checkpoint**: Can you create activities and start executions via API? Do all 17 endpoints work correctly?

### API Summary

**Total Endpoints: 17**
- Authentication: 4 endpoints
- Activities: 5 endpoints
- Executions: 5 endpoints  
- Health: 3 endpoints

### Testing Strategy

Run tests with: `pytest tests/integration/test_api.py -v --cov=backend`

Target: 80%+ code coverage for all API routes.

---

## Phase 3: Message Queue & Celery Setup (Week 4)

### Goal
Set up asynchronous task processing with Celery and RabbitMQ.

### Tasks

**3.1 Configure Celery**

Create `backend/workflow_engine/celery_app.py`:
- Initialize Celery app
- Configure RabbitMQ broker
- Configure Redis result backend
- Set up task routing

**3.2 Create Basic Task**

Create `backend/workflow_engine/tasks.py`:
- `@app.task` decorator
- Simple test task: `add(x, y)`
- Test task execution

**3.3 Update API to Publish Tasks**

Modify `executions.py`:
- After creating execution record
- Publish message to RabbitMQ
- Return execution ID immediately (don't wait)

**3.4 Create Worker Startup Script**

Create `backend/workflow_engine/worker.py`:
- Start Celery worker
- Configure concurrency
- Add logging

**3.5 Test Async Execution**
- Start worker: `celery -A backend.workflow_engine.celery_app worker -l info`
- Create execution via API
- Verify task is received by worker

**Checkpoint**: Can you submit an execution and see it picked up by Celery worker?

---

## Phase 4: SSH Execution Engine (Week 5-6)

### Goal
Implement SSH connection and command execution logic.

### Tasks

**4.1 Create SSH Client Wrapper**

Create `backend/command_executor/ssh_client.py`:
- Class `SSHClient` wrapping Paramiko
- Methods:
  - `connect()` - Establish SSH connection
  - `execute_command(cmd, expect_prompt, timeout)` - Run command
  - `disconnect()` - Close connection
- Handle timeouts and errors
- Support jump host (OSS) connections

**4.2 Implement Connection Pooling**

Create `backend/command_executor/connection_pool.py`:
- Pool of SSH connections (max 100)
- Reuse connections when possible
- Close idle connections after 5 minutes
- Thread-safe implementation

**4.3 Create Command Executor**

Create `backend/command_executor/executor.py`:
- Class `CommandExecutor`
- Initialize `State_Data_Map` with node parameters
- Method `execute_sequence(commands, ssh_client)`
- Resolve variables (<<<node_ip>>>, <<<custom_var>>>)
- Handle control flow (on_success, on_failure, GOTO)
- Store command results

**4.4 Implement Authentication Plugins**

Create `backend/command_executor/auth_plugins/`:
- `base.py` - `AuthenticationPlugin` abstract class
- `direct_ssh.py` - Username/password auth
- `jump_host.py` - Two-hop SSH
- `key_based.py` - SSH key authentication
- `iam.py` - IAM-based auth (placeholder)

**4.5 Write Unit Tests**

Create `tests/unit/test_ssh_client.py`:
- Mock Paramiko for testing
- Test command execution
- Test timeout handling
- Test connection pooling

**Checkpoint**: Can you SSH to a real/mock device and execute commands?

---

## Phase 5: Parser Framework (Week 7)

### Goal
Implement parser system for extracting data from command outputs.

### Tasks

**5.1 Create Parser Base Class**

Create `backend/parser_framework/base_parser.py`:
- Abstract class `BaseParser`
- Methods:
  - `parse(output: str) -> ParseResult`
  - `validate_output(output: str) -> bool`
- `ParseResult` dataclass with:
  - extracted_data (dict)
  - state_variables (dict)
  - both (dict)

**5.2 Create Parser Registry**

Create `backend/parser_framework/registry.py`:
- `ParserRegistry` class
- `@ParserRegistry.register(name, domain)` decorator
- `get_parser(name, domain)` method
- Dynamic parser loading

**5.3 Implement Parser Types**

Create parsers:
- `backend/parser_framework/regex_parser.py` - Regex-based parsing
- `backend/parser_framework/table_parser.py` - Table parsing
- `backend/parser_framework/json_parser.py` - JSON parsing
- `backend/parser_framework/xml_parser.py` - XML parsing

**5.4 Integrate Parsers with Executor**

Update `CommandExecutor`:
- After executing command
- Load parser from registry
- Apply parser to output
- Merge `state_variables` into `State_Data_Map`
- Store `extracted_data` for output report

**5.5 Write Parser Tests**

Create `tests/unit/test_parsers.py`:
- Test each parser type
- Test field destination (output/state/both)
- Test parser registration

**Checkpoint**: Can you parse command output and extract fields?

---

## Phase 6: Workflow Orchestration (Week 8-9)

### Goal
Implement end-to-end workflow execution with parallel processing.

### Tasks

**6.1 Create Workflow Orchestrator Task**

Create `backend/workflow_engine/orchestrator.py`:
- `@app.task` function `execute_automation_workflow(execution_id)`
- Load execution context from database
- Load activity configuration
- Create per-node tasks
- Handle execution modes (sequential, parallel, batch)

**6.2 Create Node Execution Task**

Create `backend/workflow_engine/node_executor.py`:
- `@app.task` function `execute_node_task(execution_id, node_data, activity_config)`
- Initialize SSH client
- Initialize command executor
- Execute command sequence
- Store results in database
- Upload logs to MinIO

**6.3 Implement Result Aggregation**

Create `backend/workflow_engine/aggregator.py`:
- Collect results from all nodes
- Generate unified output report
- Calculate summary statistics
- Update execution status

**6.4 Handle Parallel Execution**

Update orchestrator:
- Use Celery `group()` for parallel execution
- Enforce max_parallelism limit
- Use `chord()` for result aggregation

**6.5 Add Error Handling**

- Retry logic for transient errors
- Isolate failures (continue on node failure)
- Store error details in database

**6.6 Write Integration Tests**

Create `tests/integration/test_workflow.py`:
- Test sequential execution
- Test parallel execution
- Test result aggregation
- Test error handling

**Checkpoint**: Can you execute a full workflow on multiple nodes in parallel?

---

## Phase 7: Scheduler (Week 10)

### Goal
Implement cron-based scheduling with Celery Beat.

### Tasks

**7.1 Configure Celery Beat**

Update `celery_app.py`:
- Configure beat scheduler
- Use database scheduler (django-celery-beat alternative)

**7.2 Create Scheduler Service**

Create `backend/scheduler/scheduler.py`:
- Poll `schedules` table every minute
- Find due schedules
- Trigger executions
- Update next_execution_at

**7.3 Add Schedule Endpoints**

Create `backend/api_gateway/routes/schedules.py`:
- `POST /api/v1/schedules` - Create schedule
- `GET /api/v1/schedules` - List schedules
- `PUT /api/v1/schedules/{id}` - Update schedule
- `DELETE /api/v1/schedules/{id}` - Delete schedule

**7.4 Write Tests**

Create `tests/unit/test_scheduler.py`:
- Test cron expression parsing
- Test schedule triggering
- Test one-time execution

**Checkpoint**: Can you schedule an automation to run at a specific time?

---

## Phase 8: Mock Device Simulator (Week 11)

### Goal
Create SSH server that mimics network devices for local testing.

### Tasks

**8.1 Create Mock SSH Server**

Create `mock-devices/simulator.py`:
- Implement SSH server using Paramiko `ServerInterface`
- Handle authentication (accept any credentials in dev mode)
- Spawn shell channel
- Return pre-configured responses

**8.2 Create Personality Configs**

Create YAML files:
- `mock-devices/personalities/cisco.yaml`
- `mock-devices/personalities/nokia.yaml`
- `mock-devices/personalities/huawei.yaml`

Each file maps commands to responses.

**8.3 Add Failure Simulation**

Update simulator:
- Configurable failure rate
- Simulate connection drops
- Simulate timeouts

**8.4 Add to Docker Compose**

Add mock-device service to `docker-compose.yml`

**Checkpoint**: Can you run automation against mock device locally?

---

## Phase 9: Visual Tools (Week 12-14)

### Goal
Create frontend UI for activity management and execution monitoring.

### Tasks

**9.1 Initialize React Project**

```bash
cd frontend
npx create-react-app orchestrmator-ui --template typescript
```

Install dependencies:
- Material-UI or Ant Design
- React Router
- Axios
- React Flow (for workflow builder)

**9.2 Create Layout & Navigation**

- App shell with sidebar
- Navigation menu
- Authentication pages (login/register)

**9.3 Activity Management Pages**

- Activity list page
- Activity create/edit form
- Activity detail view

**9.4 Execution Dashboard**

- Execution list with filtering
- Execution detail page
- Real-time status updates (WebSocket)
- Result viewer

**9.5 Visual Parser Builder** (Optional)

- Monaco editor for command output
- Highlight and select fields
- Generate parser code
- Test parser with examples

**9.6 Visual Workflow Builder** (Optional)

- React Flow canvas
- Drag-drop command blocks
- Connect blocks (control flow)
- Generate YAML from visual design

**Checkpoint**: Can you manage activities and monitor executions from UI?

---

## Phase 10: Advanced Features (Week 15-20)

### Tasks

**10.1 Dry-Run Mode**
- Execute without SSH connections
- Use example outputs
- Generate simulation report

**10.2 Execution Control (Pause/Wait)**
- Pause commands for manual verification
- Wait commands with conditions
- Resume/skip actions from UI

**10.3 Event-Driven Triggers**
- Microsoft Teams bot adapter
- Email trigger (IMAP monitoring)
- Webhook endpoints
- Kafka consumer

**10.4 Time Window Enforcement**
- Configure execution windows per activity
- Validate execution time
- Auto-schedule to next window

**10.5 Component Reusability**
- Reusable command sequences
- Template library
- Import/export configurations

**10.6 Advanced Batching**
- Node-based batching
- Server-based batching
- Topology-aware batching

**10.7 CLI Command Generator**
- Generate all commands upfront
- Export to markdown/text
- Show expected prompts

---

## Phase 11: Testing & Quality (Week 21-22)

### Tasks

**11.1 Property-Based Testing**

Use Hypothesis to write tests for:
- Request validation correctness
- Execution record creation
- Parallel execution concurrency
- State data accumulation
- Parser data extraction
- Output report generation

**11.2 End-to-End Testing**
- Playwright/Selenium tests for UI
- Full workflow tests (API → Worker → DB → UI)

**11.3 Load Testing**
- Test with 200 parallel nodes
- Stress test API endpoints
- Measure response times

**11.4 Code Quality**
- Set up pre-commit hooks
- Run linters (ruff, black, mypy)
- Achieve 80%+ test coverage

---

## Phase 12: Deployment & DevOps (Week 23-25)

### Tasks

**12.1 Containerize Application**
- Create Dockerfile for API
- Create Dockerfile for Worker
- Multi-stage builds
- Optimize image size

**12.2 Create Kubernetes Manifests**

In `infrastructure/kubernetes/`:
- Deployments (API, Worker, Beat)
- Services
- ConfigMaps
- Secrets
- StatefulSets (PostgreSQL, Redis, RabbitMQ)
- Ingress

**12.3 Set Up CI/CD**

Create `.github/workflows/` or `.gitlab-ci.yml`:
- Build pipeline (lint, test, build)
- Deploy pipeline (dev, staging, prod)
- Automated migrations
- Smoke tests after deployment

**12.4 Infrastructure as Code**

Use Terraform:
- Provision cloud resources (EKS, RDS, ElastiCache)
- Configure networking (VPC, subnets, security groups)
- Set up monitoring (CloudWatch, Prometheus)

**12.5 Monitoring & Observability**
- Set up Prometheus + Grafana
- Create dashboards
- Configure alerts
- Add distributed tracing (OpenTelemetry)

---

## Phase 13: Documentation & Handoff (Week 26-27)

### Tasks

**13.1 User Documentation**
- User guide (how to create activities)
- API documentation (OpenAPI)
- Video tutorials

**13.2 Developer Documentation**
- Architecture diagrams
- Code walkthrough
- Contribution guide
- Deployment guide

**13.3 Operations Runbook**
- Common issues and solutions
- Scaling guidelines
- Backup and recovery
- Security best practices

**13.4 Training**
- Train network engineers on creating activities
- Train operators on monitoring executions
- Train developers on extending the system

---

## Development Best Practices

### Daily
- Write tests for new code
- Run linters before committing
- Update documentation
- Review code with team

### Weekly
- Team sync meeting
- Demo working features
- Review architecture decisions
- Plan next week's tasks

### Monthly
- Code review all changes
- Security audit
- Performance benchmarking
- User feedback session

---

## Success Criteria

After completing all phases, you should have:

✅ Web UI for managing activities and executions  
✅ REST API with authentication  
✅ Parallel execution on up to 200 nodes  
✅ Parser framework with multiple parser types  
✅ Scheduling system (cron-based)  
✅ Mock device simulator for local testing  
✅ Docker Compose for local development  
✅ Kubernetes deployment for production  
✅ CI/CD pipeline  
✅ Comprehensive test suite (unit, integration, e2e)  
✅ Documentation (user, developer, operations)  

---

## Resource Estimates

- **Backend Development**: 50% of time
- **Frontend Development**: 20% of time
- **DevOps & Infrastructure**: 15% of time
- **Testing & Quality**: 10% of time
- **Documentation**: 5% of time

---

## Risk Mitigation

- **SSH Connection Issues**: Build mock device simulator early
- **Scaling Challenges**: Load test early and often
- **Complex Parsers**: Start with simple regex, iterate
- **UI Complexity**: Use established component libraries
- **Deployment Issues**: Practice deployments in dev environment

---

This roadmap provides a clear path from zero to a production-ready telecom automation platform. Good luck building OrchestrMator! 🚀
