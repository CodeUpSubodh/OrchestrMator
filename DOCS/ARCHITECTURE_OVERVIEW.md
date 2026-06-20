# OrchestrMator - Architecture Overview

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                              │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  React Web Application (Port 3000)                                │  │
│  │  - Activity Management UI                                         │  │
│  │  - Execution Dashboard                                            │  │
│  │  - Visual Parser Builder                                          │  │
│  │  - Visual Workflow Builder                                        │  │
│  │  - Real-time Status Updates (WebSocket)                           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │ HTTP/WebSocket
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY LAYER                               │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application (Port 8000)                                  │  │
│  │  - REST API Endpoints (/api/v1/*)                                │  │
│  │  - Authentication & Authorization (JWT)                           │  │
│  │  - Request Validation (Pydantic)                                  │  │
│  │  - CORS, Rate Limiting                                            │  │
│  │  - WebSocket for Real-time Updates                                │  │
│  │  - OpenAPI Documentation (/docs)                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────┬───────────────────────────────────┬───────────────────────┘
              │                                   │
              ▼                                   ▼
┌─────────────────────────────┐    ┌─────────────────────────────────────┐
│   MESSAGE BROKER            │    │    CACHE & SESSION STORE            │
│   RabbitMQ (Port 5672)      │    │    Redis (Port 6379)                │
│   - automation_requests     │    │    - Session data                   │
│   - node_executions         │    │    - Execution progress             │
│   - priority_executions     │    │    - Pause states                   │
└─────────────┬───────────────┘    └─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW ENGINE LAYER                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Celery Workers                                                   │  │
│  │  ┌────────────────────┐  ┌────────────────────┐                 │  │
│  │  │ Workflow           │  │ Node Execution     │                 │  │
│  │  │ Orchestrator       │  │ Worker             │                 │  │
│  │  │ - Receive request  │  │ - SSH connection   │                 │  │
│  │  │ - Load activity    │  │ - Command exec     │                 │  │
│  │  │ - Distribute tasks │  │ - Parse output     │                 │  │
│  │  │ - Aggregate results│  │ - Store results    │                 │  │
│  │  └────────────────────┘  └────────────────────┘                 │  │
│  │                                                                   │  │
│  │  Celery Beat (Scheduler)                                         │  │
│  │  - Cron-based execution                                          │  │
│  │  - One-time scheduled runs                                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────┬─────────────────────────────────────┬─────────────────────┘
            │                                     │
            ▼                                     ▼
┌───────────────────────────┐         ┌──────────────────────────────────┐
│  EXECUTION ENGINE         │         │  PARSER FRAMEWORK                │
│  ┌─────────────────────┐  │         │  ┌────────────────────────────┐ │
│  │ SSH Client          │  │         │  │ Parser Registry            │ │
│  │ - Paramiko wrapper  │  │         │  │ - Dynamic loading          │ │
│  │ - Connection pool   │  │         │  │ - BaseParser interface     │ │
│  │ - Jump host support │  │         │  │                            │ │
│  │ - Auth plugins      │  │         │  │ Parser Types:              │ │
│  └─────────────────────┘  │         │  │ - Regex Parser             │ │
│  ┌─────────────────────┐  │         │  │ - Table Parser             │ │
│  │ Command Executor    │  │         │  │ - JSON Parser              │ │
│  │ - Command sequence  │  │         │  │ - XML Parser               │ │
│  │ - State management  │  │         │  │ - Custom Parsers           │ │
│  │ - Variable resolve  │  │         │  └────────────────────────────┘ │
│  │ - Control flow      │  │         └──────────────────────────────────┘
│  └─────────────────────┘  │
└───────────┬───────────────┘
            │
            ▼ SSH (Port 22)
┌───────────────────────────────────────────────────────────────────────┐
│                     NETWORK DEVICES (Target Nodes)                    │
│  Cisco Routers  │  Nokia RAN  │  Huawei Switches  │  Ericsson BSC    │
└───────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          DATA PERSISTENCE LAYER                          │
│  ┌──────────────────────┐  ┌──────────────────────────────────────┐   │
│  │ PostgreSQL (5432)    │  │ MinIO/S3 (9000)                      │   │
│  │ - users              │  │ - Command logs                       │   │
│  │ - activities         │  │ - Execution outputs                  │   │
│  │ - executions         │  │ - Parser results                     │   │
│  │ - node_results       │  │ - Large files                        │   │
│  │ - command_results    │  └──────────────────────────────────────┘   │
│  │ - parsers            │                                              │
│  │ - schedules          │                                              │
│  │ - audit_logs         │                                              │
│  └──────────────────────┘                                              │
└─────────────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     CONFIGURATION REPOSITORY                             │
│  Git Repository (File System)                                           │
│  - activities/*.yaml  (Activity configurations)                         │
│  - parsers/*.py       (Parser implementations)                          │
│  - templates/*.yaml   (Command templates)                               │
│  - Version controlled, CI/CD validated                                  │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     OPTIONAL: EVENT TRIGGERS                             │
│  - Microsoft Teams Bot    - Email Monitor (IMAP)                        │
│  - Webhooks (ServiceNow)  - Kafka Consumer                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. **Frontend (React)**
**Purpose**: User interface for interacting with the system

**Components**:
- Activity management (create/edit/delete activities)
- Execution dashboard (start/monitor/view executions)
- Visual parser builder (create parsers visually)
- Visual workflow builder (drag-drop command design)
- Real-time monitoring (WebSocket updates)

**Technology**: React 18, TypeScript, Material-UI/Ant Design, React Flow, WebSocket

---

### 2. **API Gateway (FastAPI)**
**Purpose**: Central entry point for all API requests

**Responsibilities**:
- REST API endpoints (CRUD operations)
- Authentication & authorization (JWT tokens)
- Request validation (Pydantic schemas)
- CORS and security middleware
- WebSocket connections for real-time updates
- Auto-generated API documentation

**Technology**: FastAPI, Pydantic, python-jose (JWT), WebSocket

---

### 3. **Message Broker (RabbitMQ)**
**Purpose**: Asynchronous task distribution

**Queues**:
- `automation_requests`: Validated automation requests
- `node_executions`: Per-node execution tasks
- `priority_executions`: Urgent automation tasks

**Technology**: RabbitMQ, AMQP protocol

---

### 4. **Cache & Session Store (Redis)**
**Purpose**: Fast data access and session management

**Use Cases**:
- User session data
- Execution progress tracking
- Pause state persistence
- Rate limiting counters
- Temporary data storage

**Technology**: Redis 7

---

### 5. **Workflow Engine (Celery)**
**Purpose**: Orchestrate multi-node automation workflows

**Components**:
- **Workflow Orchestrator**: Main task that coordinates execution
- **Node Execution Workers**: Execute commands on individual nodes
- **Celery Beat**: Scheduler for cron-based automations

**Technology**: Celery, RabbitMQ (broker), Redis (result backend)

---

### 6. **Execution Engine**
**Purpose**: SSH connection and command execution

**Components**:
- **SSH Client**: Paramiko wrapper with connection pooling
- **Command Executor**: Execute command sequences with state management
- **Authentication Plugins**: Support multiple auth methods (password, key, IAM)

**Technology**: Paramiko, connection pooling, retry logic

---

### 7. **Parser Framework**
**Purpose**: Extract structured data from command outputs

**Components**:
- **Parser Registry**: Dynamic parser loading
- **BaseParser**: Abstract interface for all parsers
- **Parser Types**: Regex, Table, JSON, XML, Custom

**Technology**: Python regex, pandas (for table parsing), custom logic

---

### 8. **Data Persistence Layer**

#### PostgreSQL Database
**Purpose**: Structured data storage

**Tables**:
- `users`: User accounts and authentication
- `activities`: Activity configurations (JSONB)
- `executions`: Execution records and status
- `node_results`: Per-node execution results
- `command_results`: Per-command execution details
- `parsers`: Parser definitions
- `schedules`: Scheduled executions
- `audit_logs`: Audit trail

**Technology**: PostgreSQL 15, SQLAlchemy ORM, Alembic migrations

#### MinIO/S3 Storage
**Purpose**: Large file storage

**Stored Data**:
- Raw command outputs (logs)
- Execution result files
- Parser outputs (large datasets)

**Technology**: MinIO (S3-compatible), boto3 SDK

---

### 9. **Configuration Repository (Git)**
**Purpose**: Version-controlled configuration management

**Structure**:
- `activities/`: YAML activity configurations
- `parsers/`: Python parser implementations
- `templates/`: Reusable command templates

**Technology**: Git, YAML validation, CI/CD hooks

---

### 10. **Event Triggers (Optional)**
**Purpose**: Trigger automations from external sources

**Sources**:
- Microsoft Teams bot commands
- Email monitoring (IMAP)
- Webhooks (ServiceNow, Jira)
- Kafka message queue

**Technology**: Adapters for each source, webhook verification

---

## Technology Stack Summary

### Backend
- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **Task Queue**: Celery
- **SSH Library**: Paramiko
- **ORM**: SQLAlchemy
- **Validation**: Pydantic
- **Testing**: pytest, Hypothesis

### Infrastructure
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Message Broker**: RabbitMQ 3.12
- **Object Storage**: MinIO (S3-compatible)
- **Containerization**: Docker, Docker Compose

### Frontend (Future)
- **Framework**: React 18
- **Language**: TypeScript
- **UI Library**: Material-UI or Ant Design
- **State Management**: Redux Toolkit or Zustand
- **Workflow Visualizer**: React Flow

### DevOps
- **Container Orchestration**: Kubernetes
- **CI/CD**: GitHub Actions / GitLab CI
- **Infrastructure as Code**: Terraform
- **Monitoring**: Prometheus, Grafana (future)

---

## Data Flow: Execution Request

```
1. User submits execution request via API
   ↓
2. API Gateway validates request (Pydantic)
   ↓
3. Create execution record in PostgreSQL
   ↓
4. Publish message to RabbitMQ (automation_requests queue)
   ↓
5. Workflow Orchestrator consumes message
   ↓
6. Load activity configuration from database
   ↓
7. Create per-node tasks → Publish to node_executions queue
   ↓
8. Node Workers consume tasks (parallel execution)
   ↓
9. For each node:
   a. SSH Client connects to device
   b. Command Executor runs command sequence
   c. Apply parsers to extract data
   d. Store results in PostgreSQL
   e. Upload logs to MinIO
   ↓
10. Workflow Orchestrator aggregates results
   ↓
11. Generate final output report
   ↓
12. Update execution status to "completed"
   ↓
13. WebSocket notifies frontend of completion
```

---

## Deployment Architecture

### Local Development
```
Docker Compose:
- postgres:15
- redis:7
- rabbitmq:3.12-management
- minio/minio
- app (FastAPI)
- worker (Celery)
- beat (Celery Beat)
```

### Production (Kubernetes)
```
Kubernetes Cluster:
- API Gateway (Deployment, 3 replicas)
- Celery Workers (Deployment, auto-scaling)
- Celery Beat (Deployment, 1 replica)
- PostgreSQL (StatefulSet or managed RDS)
- Redis (StatefulSet or managed ElastiCache)
- RabbitMQ (StatefulSet or managed MQ)
- MinIO (StatefulSet or managed S3)
- Ingress Controller (NGINX)
- Horizontal Pod Autoscaler
```

---

## Security Architecture

### Authentication & Authorization
- JWT tokens (access + refresh)
- Role-based access control (admin, engineer, viewer)
- Password hashing (bcrypt)
- Account lockout after failed attempts

### Network Security
- API rate limiting
- CORS configuration
- HTTPS only (production)
- Firewall rules for SSH access

### Data Security
- Encrypted passwords in database
- Secrets management (Kubernetes secrets)
- Audit logging for all actions
- SSH key rotation support

---

## Scalability Strategy

### Horizontal Scaling
- API Gateway: Add more FastAPI instances
- Celery Workers: Add more worker processes
- Database: Read replicas for queries

### Performance Optimization
- Connection pooling (SSH, Database)
- Redis caching for frequent queries
- Async I/O for API endpoints
- Batch processing for bulk operations

### Resource Limits
- Max parallelism: 200 simultaneous SSH connections
- Request rate limiting: 100 req/min per user
- Execution timeout: Configurable per activity

---

## Monitoring & Observability (Future)

- **Logs**: Structured JSON logging to ELK stack
- **Metrics**: Prometheus metrics (execution count, duration, errors)
- **Tracing**: OpenTelemetry for distributed tracing
- **Dashboards**: Grafana dashboards for system health
- **Alerts**: Alert on failures, high latency, resource exhaustion

---

This architecture provides a clear separation of concerns, scalability, and maintainability for OrchestrMator!
