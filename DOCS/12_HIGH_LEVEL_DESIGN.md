# High-Level Design (HLD): Cloud-Native Telecom Automation Platform

## Document Information
- **Version**: 1.0
- **Date**: June 9, 2026
- **Purpose**: Define the high-level architecture, system components, and interactions for the modernized telecom automation platform

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Style](#architecture-style)
3. [Component Diagram](#component-diagram)
4. [Data Flow](#data-flow)
5. [Deployment Architecture](#deployment-architecture)
6. [Technology Stack](#technology-stack)
7. [Security Architecture](#security-architecture)
8. [Integration Architecture](#integration-architecture)
9. [Scalability and Performance](#scalability-and-performance)
10. [Disaster Recovery](#disaster-recovery)

---

## 1. System Overview

### 1.1 Purpose
The Cloud-Native Telecom Automation Platform enables network engineers to create, execute, and monitor telecom device automation workflows through both GUI and CLI interfaces. It replaces a legacy Python 2.7 system with modern, scalable architecture supporting local development, Git-based configuration management, and AI-assisted automation creation.

### 1.2 Key Capabilities
- **On-Demand & Scheduled Execution**: Execute automations immediately or schedule for future execution
- **Parallel Processing**: Execute commands across 100+ network nodes concurrently
- **Visual Tools**: Build parsers and activities through intuitive GUI without manual coding
- **Local Testing**: Test automations against mock devices before production deployment
- **Real-Time Monitoring**: Track execution progress with live status updates
- **Git-Based Configuration**: Version control all automation configurations
- **AI Assistance**: Generate parsers automatically from command output examples
- **Multi-Tenancy**: Role-based access control for team collaboration

### 1.3 Non-Functional Requirements
- **Performance**: Support 100+ parallel node executions with <10 minute completion
- **Availability**: 99.5% uptime with auto-recovery from transient failures
- **Scalability**: Horizontal scaling for API and workers, vertical for databases
- **Security**: JWT/OAuth authentication, RBAC, audit logging, encrypted credentials
- **Maintainability**: Modular design, comprehensive testing, automated CI/CD

---

## 2. Architecture Style

### 2.1 Modular Monolith (Phase 1)
**Decision**: Start with modular monolith architecture, design for microservices evolution

**Rationale**:
- Simpler initial development and deployment
- Lower operational complexity for learning phase
- Easier debugging and testing
- Clear module boundaries enable future extraction to microservices
- Reduced network latency between components

**Module Boundaries**:
```
backend/
├── api_gateway/           # API routes, request validation
├── workflow_engine/       # Execution orchestration, Celery tasks
├── parser_framework/      # Parser registry, base classes, implementations
├── command_executor/      # SSH client, command execution, state management
├── config_manager/        # Activity and parser configuration management
├── auth_service/          # Authentication, authorization, audit logging
├── scheduler/             # Cron-based scheduling, schedule management
├── additional_modules/    # Post-execution modules (email, CSV merger)
└── shared/                # Common utilities, database models, schemas
```

### 2.2 Event-Driven Architecture
**Message Broker**: RabbitMQ with priority queues for async task distribution

**Queue Structure**:
- `automation_requests` - Validated execution requests
- `node_executions` - Per-node execution tasks
- `priority_executions` - Urgent automations (bypass normal queue)
- `dlq_*` - Dead letter queues for failed messages

**Event Flow**:
1. API Gateway validates request → publishes to `automation_requests`
2. Workflow Orchestrator consumes → creates per-node tasks → publishes to `node_executions`
3. Worker pool consumes node tasks → executes → publishes results
4. Result Aggregator collects → generates report → triggers Additional Modules

### 2.3 Future Microservices Architecture (Phase 2)
When scale demands (1000+ concurrent executions), extract to microservices:

**Service Boundaries**:
- **API Gateway Service** - External API, request routing, authentication
- **Execution Service** - Workflow orchestration, execution management
- **Device Communication Service** - SSH connections, command execution
- **Parser Service** - Parser execution, AI-powered generation
- **Configuration Service** - Activity/parser management, Git sync
- **Notification Service** - Email, webhooks, real-time updates
- **Analytics Service** - Metrics, logs, execution history

**Communication**: Service mesh (Istio) for service-to-service communication, observability, and traffic management

---

## 3. Component Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                                    │
├──────────────────────────┬──────────────────────────────────────────────┤
│   Web Application        │         CLI Tool                             │
│   (React + TypeScript)   │    (Python Click + API Client)               │
└──────────────────────────┴──────────────────────────────────────────────┘
                                      │
                                      ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                       API GATEWAY (FastAPI)                              │
├─────────────────────────────────────────────────────────────────────────┤
│  • Request Validation (Pydantic)                                         │
│  • Authentication/Authorization (JWT/OAuth)                              │
│  • Rate Limiting (Redis-based)                                           │
│  • WebSocket Server (Real-time updates)                                 │
│  • OpenAPI Documentation                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
┌──────────────────────┐  ┌──────────────────┐  ┌────────────────────┐
│  Configuration       │  │  Execution       │  │  Parser Builder    │
│  Manager             │  │  Manager         │  │  Service           │
├──────────────────────┤  ├──────────────────┤  ├────────────────────┤
│ • Activity CRUD      │  │ • Validation     │  │ • Structure        │
│ • Parser CRUD        │  │ • Publish to MQ  │  │   Detection        │
│ • Template Library   │  │ • Status Query   │  │ • Code Generation  │
│ • Git Sync           │  │ • Result Fetch   │  │ • AI Integration   │
└──────────────────────┘  └──────────────────┘  └────────────────────┘
         │                         │                      │
         └─────────────────────────┼──────────────────────┘
                                   ↓
                      ┌──────────────────────────┐
                      │   MESSAGE BROKER         │
                      │   (RabbitMQ)             │
                      ├──────────────────────────┤
                      │  Queues:                 │
                      │  • automation_requests   │
                      │  • node_executions       │
                      │  • priority_executions   │
                      └──────────────────────────┘
                                   │
                ┌──────────────────┴───────────────────┐
                ↓                                      ↓
┌──────────────────────────────┐      ┌──────────────────────────────┐
│  WORKFLOW ORCHESTRATOR       │      │  SCHEDULER SERVICE           │
│  (Celery Beat + Workers)     │      │  (Celery Beat)               │
├──────────────────────────────┤      ├──────────────────────────────┤
│ • Parse Execution Request    │      │ • Poll Schedules (1/min)     │
│ • Create Node Tasks          │      │ • Trigger Due Executions     │
│ • Distribute via Celery      │      │ • Update Next Execution      │
│ • Aggregate Results          │      └──────────────────────────────┘
│ • Trigger Additional Modules │
└──────────────────────────────┘
                │
                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                    WORKER POOL (Celery Workers)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │  Node Worker 1 │  │  Node Worker 2 │  │  Node Worker N │            │
│  │  • SSH Connect │  │  • SSH Connect │  │  • SSH Connect │            │
│  │  • Execute Cmd │  │  • Execute Cmd │  │  • Execute Cmd │            │
│  │  • Parse Output│  │  • Parse Output│  │  • Parse Output│            │
│  │  • Store Result│  │  • Store Result│  │  • Store Result│            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┼──────────────────┐
                ↓                  ↓                  ↓
┌──────────────────┐  ┌─────────────────────┐  ┌───────────────────────┐
│  COMMAND         │  │  PARSER             │  │  STATE MANAGER        │
│  EXECUTOR        │  │  FRAMEWORK          │  │                       │
├──────────────────┤  ├─────────────────────┤  ├───────────────────────┤
│ • SSH Client     │  │ • Parser Registry   │  │ • State_Data_Map      │
│ • Prompt Detect  │  │ • Base Parser       │  │ • Variable Resolution │
│ • Retry Logic    │  │ • Regex Parser      │  │ • DYNAMIC_PARS        │
│ • Jump Host      │  │ • Table Parser      │  └───────────────────────┘
│ • Timeout Handle │  │ • JSON/XML Parser   │
└──────────────────┘  └─────────────────────┘
         │                     │
         └─────────────────────┼─────────────────────────┐
                               ↓                         ↓
                  ┌─────────────────────┐   ┌──────────────────────────┐
                  │  TARGET DEVICES     │   │  MOCK DEVICE SIMULATOR   │
                  │  (via SSH/OSS)      │   │  (SSH Server - Local)    │
                  ├─────────────────────┤   ├──────────────────────────┤
                  │ • Cisco IOS         │   │ • Personality Configs    │
                  │ • Nokia SROS        │   │ • Command-Response Map   │
                  │ • Huawei VRP        │   │ • Failure Simulation     │
                  │ • Ericsson          │   │ • Latency Injection      │
                  └─────────────────────┘   └──────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                       │
├──────────────────────┬──────────────────────┬───────────────────────────┤
│  PostgreSQL          │  Redis               │  MinIO (S3)               │
│  (Primary Data)      │  (Cache + Pub/Sub)   │  (Object Storage)         │
├──────────────────────┼──────────────────────┼───────────────────────────┤
│ • Activities         │ • Session Cache      │ • Execution Logs          │
│ • Executions         │ • Rate Limit         │ • Output Reports          │
│ • Node Results       │ • Execution Status   │ • Archived Results        │
│ • Parsers            │ • WebSocket Pub/Sub  │ • Configuration Backups   │
│ • Users & Roles      │ • Task State         │                           │
│ • Schedules          │ • API Response Cache │                           │
│ • Audit Logs         │                      │                           │
└──────────────────────┴──────────────────────┴───────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY LAYER                                   │
├──────────────────────┬──────────────────────┬───────────────────────────┤
│  Prometheus          │  Structured Logging  │  Distributed Tracing      │
│  (Metrics)           │  (structlog)         │  (OpenTelemetry/Jaeger)   │
├──────────────────────┼──────────────────────┼───────────────────────────┤
│ • Execution Metrics  │ • JSON Logs          │ • Request Tracing         │
│ • System Health      │ • Error Context      │ • Cross-Service Spans     │
│ • Performance        │ • Audit Trail        │ • Latency Analysis        │
│ • Alerting Rules     │ • ELK/Loki           │ • Bottleneck Detection    │
└──────────────────────┴──────────────────────┴───────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL INTEGRATIONS                                 │
├──────────────────────┬──────────────────────┬───────────────────────────┤
│  Git Repository      │  SMTP Server         │  OAuth/SAML Provider      │
│  (Configuration)     │  (Notifications)     │  (Authentication)         │
├──────────────────────┼──────────────────────┼───────────────────────────┤
│ • Activity Configs   │ • Execution Summary  │ • SSO Integration         │
│ • Parser Definitions │ • Alert Emails       │ • Token Validation        │
│ • CI/CD Validation   │ • Report Delivery    │ • User Provisioning       │
└──────────────────────┴──────────────────────┴───────────────────────────┘
```

---

## 4. Data Flow

### 4.1 On-Demand Execution Flow

```
[User] → [Web UI/CLI]
   ↓
   1. Select Activity + Upload Input Sheet
   ↓
[API Gateway] /api/v1/executions (POST)
   ↓
   2. Validate JWT Token → Extract User Context
   3. Validate Input Schema (Pydantic)
   4. Check RBAC Permissions (execute_automation)
   ↓
[Execution Manager]
   ↓
   5. Create Execution Record (PostgreSQL)
   6. Transform Input → node_pars for each node
   7. Publish Message to automation_requests queue
   8. Return execution_id to client
   ↓
[RabbitMQ] automation_requests queue
   ↓
[Workflow Orchestrator] (Celery Consumer)
   ↓
   9. Load Activity Configuration from DB
   10. Create Per-Node Tasks (Celery group/chain based on mode)
   11. Publish to node_executions queue
   12. Update Execution Status → "running"
   13. Publish status to Redis Pub/Sub → WebSocket
   ↓
[Worker Pool] (Multiple Celery Workers)
   ↓ (Per Node Task)
   14. Initialize State_Data_Map with node_pars
   15. Load Command Sequence from Activity Config
   ↓
[Command Executor]
   ↓
   16. Connect via SSH (direct or jump host)
   17. For each command in sequence:
       a. Resolve <<<variables>>> from State_Data_Map
       b. Send command to device
       c. Wait for prompt (regex matching)
       d. Capture output
       e. Load Parser from Registry
       f. Apply Parser → Extract data
       g. Update State_Data_Map with state_variables
       h. Store extracted_data for output
       i. Evaluate on_success/on_failure → GOTO logic
   18. Close SSH Connection
   19. Store Node Result to PostgreSQL
   20. Return extracted_data + execution_status
   ↓
[Result Aggregator] (Celery Chord Callback)
   ↓
   21. Collect All Node Results
   22. Generate Output_Sheet (structured report)
   23. Store Report in MinIO
   24. Update Execution Status → "completed"
   25. Publish status to Redis Pub/Sub → WebSocket
   ↓
[Additional Modules]
   ↓
   26. Execute Configured Modules:
       - Email Notification (send summary)
       - CSV Merger (combine outputs)
       - Metrics Calculator (aggregate stats)
   27. Attach Module Outputs to Execution
   ↓
[Client] receives completion notification
   28. Download Output_Sheet
   29. View Results in Dashboard
```

### 4.2 Scheduled Execution Flow

```
[Scheduler Service] (Celery Beat - runs every 1 minute)
   ↓
   1. Query schedules table WHERE next_execution_at <= NOW()
   2. For each due schedule:
      a. Load schedule details (activity_id, input_data, recurrence)
      b. Publish to automation_requests queue (same as on-demand)
      c. Calculate next_execution_at (if recurring)
      d. Update schedules table
   ↓
[Workflow continues same as on-demand from step 9]
```

### 4.3 Parser Creation Flow (Visual Builder)

```
[User] → [Visual Parser Builder UI]
   ↓
   1. Paste Command Output Examples
   ↓
[Parser Builder Service] /api/v1/parsers/detect-structure (POST)
   ↓
   2. Analyze Output Structure
      - Detect table format (fixed-width/delimited)
      - Detect JSON/XML structure
      - Detect key-value pairs
   3. Return structure_type + confidence
   ↓
[UI] Display detected structure with highlighting
   ↓
   4. User selects fields by clicking/dragging
   5. User configures:
      - Field name
      - Destination (output/state/both)
      - Data type
   ↓
[Parser Builder Service] /api/v1/parsers/generate (POST)
   ↓
   6. Generate Python Parser Code from selections
   7. Generate Unit Tests with examples
   8. Return generated code + preview results
   ↓
[UI] Display generated code + test preview
   ↓
   9. User tests with additional examples
   10. User saves parser
   ↓
[Configuration Manager]
   ↓
   11. Store parser in PostgreSQL
   12. Commit parser to Git repository
   13. Register in ParserRegistry
   14. Return parser_id
```

### 4.4 Configuration Sync Flow (Git to Database)

```
[Developer] → [Git Repository]
   ↓
   1. Commit Activity YAML to activities/<domain>/
   2. Push to remote repository
   ↓
[GitHub Actions] (CI/CD Workflow)
   ↓
   3. Checkout repository
   4. Run YAML Schema Validation
   5. Run Parser Reference Checks
   6. Run Variable Consistency Checks
   7. If validation fails → Block merge + notify
   ↓
   8. On merge to main branch:
      Trigger Sync Workflow
   ↓
[Sync Service] sync_to_db.py
   ↓
   9. Pull latest configs from Git
   10. Parse YAML files
   11. For each activity:
       a. Check if exists in DB (by name)
       b. Compare git_commit_sha
       c. If changed → Update DB record
       d. Store git_commit_sha for tracking
   12. Log sync results
   ↓
[Database] activities table updated
   ↓
[API Gateway] Configuration available for execution
```

---

## 5. Deployment Architecture

### 5.1 Local Development Environment

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Docker Compose                                   │
├────────────────┬────────────────┬────────────────┬──────────────────┤
│  FastAPI       │  Celery Worker │  PostgreSQL    │  RabbitMQ        │
│  (Port 8000)   │  (3 workers)   │  (Port 5432)   │  (Port 5672)     │
├────────────────┼────────────────┼────────────────┼──────────────────┤
│  Redis         │  MinIO         │  Mock Device   │  React Dev       │
│  (Port 6379)   │  (Port 9000)   │  (Port 2222)   │  (Port 3000)     │
└────────────────┴────────────────┴────────────────┴──────────────────┘

All services networked via Docker bridge network
Volumes for persistent data (postgres, rabbitmq, minio)
Hot-reload enabled for API and frontend
```

### 5.2 Kubernetes Production Deployment

```
┌───────────────────────────────────────────────────────────────────────┐
│                         KUBERNETES CLUSTER                             │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                     INGRESS CONTROLLER                            │ │
│  │  (NGINX Ingress + TLS Termination)                               │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                 │                                      │
│  ┌──────────────────────────────┴─────────────────────────────────┐  │
│  │                    NAMESPACE: automation-platform               │  │
│  │                                                                  │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  API GATEWAY DEPLOYMENT                                      │  │  │
│  │  │  • Replicas: 3 (HPA: 3-10 based on CPU 70%)                │  │  │
│  │  │  • Resources: 1 CPU, 2Gi RAM (request), 2 CPU, 4Gi (limit)  │  │  │
│  │  │  • Service: ClusterIP (Port 8000)                           │  │  │
│  │  │  • Probes: liveness /health, readiness /ready               │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  CELERY WORKER DEPLOYMENT                                    │  │  │
│  │  │  • Replicas: 5 (HPA: 2-20 based on queue depth via KEDA)   │  │  │
│  │  │  • Resources: 2 CPU, 4Gi RAM (request), 4 CPU, 8Gi (limit)  │  │  │
│  │  │  • Concurrency: 10 tasks per worker                         │  │  │
│  │  │  • No Service (worker only)                                  │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  CELERY BEAT DEPLOYMENT (Scheduler)                          │  │  │
│  │  │  • Replicas: 1 (singleton)                                   │  │  │
│  │  │  • Resources: 0.5 CPU, 512Mi RAM                             │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  POSTGRESQL STATEFULSET                                      │  │  │
│  │  │  • Replicas: 1 (primary) + 2 (read replicas)                │  │  │
│  │  │  • Storage: 100Gi PVC (ReadWriteOnce)                        │  │  │
│  │  │  • Backup: Daily to S3 via CronJob                           │  │  │
│  │  │  • Service: Headless for StatefulSet                         │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  RABBITMQ STATEFULSET                                        │  │  │
│  │  │  • Replicas: 3 (cluster mode)                                │  │  │
│  │  │  • Storage: 50Gi PVC per replica                             │  │  │
│  │  │  • Service: ClusterIP (Port 5672) + Management (15672)       │  │  │
│  │  │  • Mirrored queues for HA                                    │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  REDIS DEPLOYMENT                                            │  │  │
│  │  │  • Replicas: 1 master + 2 replicas (Redis Sentinel)         │  │  │
│  │  │  • Service: ClusterIP (Port 6379)                            │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  MINIO STATEFULSET (S3-compatible)                           │  │  │
│  │  │  • Replicas: 4 (distributed mode)                            │  │  │
│  │  │  • Storage: 500Gi PVC per replica                            │  │  │
│  │  │  • Service: ClusterIP (Port 9000)                            │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │  FRONTEND DEPLOYMENT (React App)                             │  │  │
│  │  │  • Replicas: 2 (HPA: 2-5 based on CPU)                      │  │  │
│  │  │  • Resources: 0.5 CPU, 512Mi RAM                             │  │  │
│  │  │  • Service: ClusterIP (Port 80)                              │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  │                                                                     │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
```

### 5.3 Multi-Environment Strategy

**Development**: Docker Compose on local machine
**Staging**: Kubernetes cluster (smaller resource limits, mock devices only)
**Production**: Kubernetes cluster (full resources, real device access)

**Promotion Flow**:
```
Local Dev → PR → CI Tests → Merge → Build Image → Deploy to Staging
          → Smoke Tests → Manual Approval → Deploy to Production
          → Health Checks (5 min) → Auto-Rollback on Failure
```

---

## 6. Technology Stack

### 6.1 Backend Stack
```
┌──────────────────────┬────────────────────────────────────────────────┐
│ Component            │ Technology Choice                              │
├──────────────────────┼────────────────────────────────────────────────┤
│ API Framework        │ FastAPI 0.100+ (async, high-performance)       │
│ Task Queue           │ Celery 5.3+ (mature, proven)                   │
│ Message Broker       │ RabbitMQ 3.12+ (reliable, feature-rich)        │
│ Database             │ PostgreSQL 15+ (JSONB, performance)            │
│ Cache & Pub/Sub      │ Redis 7.0+ (fast, versatile)                   │
│ Object Storage       │ MinIO (S3-compatible, on-prem friendly)        │
│ SSH Library          │ Paramiko 3.0+ (pure Python, well-tested)       │
│ ORM                  │ SQLAlchemy 2.0+ (async support)                │
│ Schema Validation    │ Pydantic 2.0+ (fast, type-safe)                │
│ Testing              │ pytest + Hypothesis (unit + property-based)    │
│ Language             │ Python 3.11+ (performance improvements)        │
└──────────────────────┴────────────────────────────────────────────────┘
```

### 6.2 Frontend Stack
```
┌──────────────────────┬────────────────────────────────────────────────┐
│ Component            │ Technology Choice                              │
├──────────────────────┼────────────────────────────────────────────────┤
│ Framework            │ React 18+ with TypeScript                      │
│ Build Tool           │ Vite 4+ (fast, modern)                         │
│ State Management     │ Redux Toolkit or Zustand                       │
│ UI Components        │ Material-UI v5 or Ant Design                   │
│ Data Fetching        │ Axios with interceptors                        │
│ Real-Time Updates    │ WebSocket (native) + React hooks               │
│ Code Editor          │ Monaco Editor (for YAML/parser code)           │
│ Charts               │ Recharts or Chart.js                           │
└──────────────────────┴────────────────────────────────────────────────┘
```

### 6.3 Infrastructure Stack
```
┌──────────────────────┬────────────────────────────────────────────────┐
│ Component            │ Technology Choice                              │
├──────────────────────┼────────────────────────────────────────────────┤
│ Containerization     │ Docker 24+ with multi-stage builds             │
│ Orchestration        │ Kubernetes 1.27+                               │
│ CI/CD                │ GitHub Actions                                 │
│ Auto-Scaling         │ HPA (CPU-based) + KEDA (queue-based)           │
│ Ingress              │ NGINX Ingress Controller                       │
│ Service Mesh         │ Istio (future microservices phase)             │
└──────────────────────┴────────────────────────────────────────────────┘
```

### 6.4 Observability Stack
```
┌──────────────────────┬────────────────────────────────────────────────┐
│ Component            │ Technology Choice                              │
├──────────────────────┼────────────────────────────────────────────────┤
│ Metrics              │ Prometheus + Grafana                           │
│ Logging              │ structlog + ELK Stack or Loki                  │
│ Tracing              │ OpenTelemetry + Jaeger                         │
│ Alerting             │ Prometheus Alertmanager + PagerDuty            │
└──────────────────────┴────────────────────────────────────────────────┘
```

---

## 7. Security Architecture

### 7.1 Authentication & Authorization

**Authentication Mechanisms**:
1. **JWT Tokens** (Primary)
   - HS256 signing algorithm
   - 24-hour expiration
   - Refresh token with 7-day expiration
   - Token claims: user_id, email, role, permissions

2. **OAuth 2.0** (Enterprise SSO)
   - Support for Google, Microsoft, Okta
   - Authorization Code flow
   - State parameter for CSRF protection

3. **SAML 2.0** (Enterprise SSO)
   - SP-initiated and IdP-initiated flows
   - Assertion encryption
   - Signature validation

**Authorization Model**:
```
Role-Based Access Control (RBAC)

Roles:
├── admin
│   ├── Permissions: ALL
│   └── Access: Full system configuration
├── engineer
│   ├── Permissions: execute_automation, create_activity, create_parser
│   └── Access: Create and execute automations
└── viewer
    ├── Permissions: view_results, view_activities
    └── Access: Read-only access

Permission Enforcement:
- API Gateway: @require_permission decorator on routes
- Database: Row-level security (RLS) for multi-tenancy
- Audit: All access attempts logged to audit_logs table
```

### 7.2 Network Security

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INTERNET                                     │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   FIREWALL / WAF        │
                    │   (Rate Limiting)       │
                    └───────────┬────────────┘
                                │
                    ┌───────────▼────────────┐
                    │   INGRESS (TLS)         │
                    │   (Certificate)         │
                    └───────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼──────┐    ┌──────────▼─────────┐    ┌──────▼──────┐
│  Frontend    │    │   API Gateway       │    │  Monitoring │
│  (Public)    │    │   (Internal)        │    │  (Internal) │
└──────────────┘    └──────────┬─────────┘    └─────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼──────┐    ┌──────────▼─────────┐    ┌──────▼──────┐
│  PostgreSQL  │    │   RabbitMQ         │    │  Redis      │
│  (Private)   │    │   (Private)        │    │  (Private)  │
└──────────────┘    └────────────────────┘    └─────────────┘

Network Policies:
- Frontend: Only accessible from Ingress
- API Gateway: Only accessible from Ingress and Workers
- Databases: Only accessible from API Gateway and Workers
- Workers: Only accessible from RabbitMQ
- No pod-to-pod traffic except via defined policies
```

### 7.3 Data Security

**Encryption**:
- **In Transit**: TLS 1.3 for all external connections, mTLS for service-to-service
- **At Rest**: 
  - Database: PostgreSQL native encryption (pg_crypto)
  - Object Storage: MinIO server-side encryption (SSE)
  - Secrets: Kubernetes Secrets encrypted with KMS

**Credential Management**:
```
Device Credentials Storage:
1. Encrypted in PostgreSQL using Fernet symmetric encryption
2. Encryption keys stored in Kubernetes Secrets
3. Keys rotated quarterly via automated process
4. Decryption only in worker memory, never logged

Secret Rotation:
- Database passwords: Quarterly
- API tokens: Quarterly
- Device credentials: Per security policy
- TLS certificates: Annual (auto-renewed via cert-manager)
```

**Audit Logging**:
```sql
audit_logs table:
- timestamp
- user_id
- action (login, execute_automation, config_change, etc.)
- resource_type, resource_id
- ip_address
- user_agent
- success (boolean)
- details (JSONB)

Retention: 1 year in database, 7 years in archive
Immutability: Append-only table, no deletes allowed
```

### 7.4 Compliance

**Security Standards**:
- OWASP Top 10 mitigations implemented
- Regular security scans (Trivy for images, Snyk for dependencies)
- Penetration testing: Annual
- Vulnerability management: Critical patches within 24 hours

**Access Controls**:
- Principle of least privilege
- Just-in-time access for production (time-limited)
- Multi-factor authentication for privileged accounts
- Session timeout: 24 hours (configurable)

---

## 8. Integration Architecture

### 8.1 External System Integrations

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AUTOMATION PLATFORM                                │
└────────┬───────────────────┬───────────────────┬─────────────────────┘
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│  Git Repository │  │  SMTP Server     │  │  OAuth/SAML         │
│  (GitHub/GitLab)│  │  (Email)         │  │  Provider           │
├─────────────────┤  ├──────────────────┤  ├─────────────────────┤
│ • Activity      │  │ • Execution      │  │ • User Auth         │
│   Configs       │  │   Notifications  │  │ • Token Validation  │
│ • Parser Defs   │  │ • Alert Emails   │  │ • Profile Sync      │
│ • CI Validation │  │ • Report         │  └─────────────────────┘
│ • Webhook       │  │   Distribution   │
│   (on push)     │  └──────────────────┘
└─────────────────┘
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌──────────────────────┐
│  Monitoring     │  │  Ticketing System    │
│  (Prometheus)   │  │  (ServiceNow/Jira)   │
├─────────────────┤  ├──────────────────────┤
│ • Metrics Pull  │  │ • Execution Link     │
│ • Alert Push    │  │ • Failure Tickets    │
└─────────────────┘  │ • CR Association     │
                     └──────────────────────┘
```

### 8.2 API Integration Patterns

**RESTful API**:
```
Base URL: https://automation.example.com/api/v1

Authentication: Bearer Token (JWT)
Content-Type: application/json

Endpoints:
GET    /activities              - List activities
POST   /activities              - Create activity
GET    /activities/{id}         - Get activity details
PUT    /activities/{id}         - Update activity
DELETE /activities/{id}         - Delete activity

POST   /executions              - Start execution
GET    /executions              - List executions
GET    /executions/{id}         - Get execution status
DELETE /executions/{id}         - Cancel execution
GET    /executions/{id}/results - Get results

POST   /parsers/generate        - Generate parser
POST   /parsers/ai-generate     - AI-generate parser
GET    /templates               - Search command templates

POST   /schedules               - Create schedule
GET    /schedules               - List schedules
DELETE /schedules/{id}          - Cancel schedule

Rate Limits:
- 100 requests/minute per user
- 1000 requests/minute per IP
- 429 Too Many Requests on limit exceed

Error Format:
{
  "error_type": "ValidationError",
  "message": "Invalid input data",
  "details": {...},
  "remediation": "Check field X",
  "request_id": "uuid"
}
```

**WebSocket API**:
```
URL: wss://automation.example.com/ws/executions/{execution_id}

Authentication: JWT token in query param ?token=xxx

Message Format:
{
  "type": "status_update",
  "execution_id": "uuid",
  "status": "running",
  "progress": 45.5,
  "node_statuses": {
    "node1": "completed",
    "node2": "running",
    "node3": "pending"
  },
  "estimated_completion": "2026-06-09T15:30:00Z",
  "timestamp": "2026-06-09T15:25:00Z"
}

Client → Server:
- Heartbeat every 30s
- Reconnect with exponential backoff on disconnect
```

**Webhook API** (Outbound):
```
Platform → External System

Events:
- execution.started
- execution.completed
- execution.failed
- schedule.triggered

Payload:
{
  "event": "execution.completed",
  "execution_id": "uuid",
  "activity_name": "Nokia_Health_Check",
  "status": "completed",
  "timestamp": "2026-06-09T15:30:00Z",
  "result_url": "https://automation.example.com/api/v1/executions/{id}/results",
  "signature": "sha256=..."
}

Security:
- HMAC signature for verification
- Retry with exponential backoff (max 5 attempts)
- Timeout: 10 seconds
```

---

## 9. Scalability and Performance

### 9.1 Horizontal Scaling

**Stateless Components** (Scale Out):
```
API Gateway:
- Current: 3 replicas
- Auto-scale: 3-10 replicas based on CPU 70% threshold
- Load balancing: Round-robin via Kubernetes Service

Celery Workers:
- Current: 5 replicas
- Auto-scale: 2-20 replicas based on RabbitMQ queue depth
- Trigger: queue_depth > 100 messages → scale up
- Cooldown: 5 minutes before scale down
```

**Stateful Components** (Scale Up):
```
PostgreSQL:
- Primary: Scale vertically (CPU, RAM, IOPS)
- Read Replicas: Scale horizontally for read queries
- Connection pooling: PgBouncer (max 100 connections)

RabbitMQ:
- Cluster mode: 3 nodes with mirrored queues
- Scale vertically per node
- Queue sharding for extreme throughput
```

### 9.2 Performance Targets

```
┌──────────────────────────────┬─────────────────────────────────────┐
│ Metric                        │ Target                              │
├──────────────────────────────┼─────────────────────────────────────┤
│ API Response Time (p95)       │ <200ms (read), <500ms (write)       │
│ Execution Latency             │ <30s from request to first node     │
│ Parallel Node Execution       │ 100 nodes in <10 minutes            │
│ Parser Execution Time         │ <200ms for 10KB output              │
│ Database Query Time (p95)     │ <50ms                               │
│ WebSocket Update Latency      │ <2 seconds                          │
│ Message Broker Throughput     │ 1000 messages/second                │
│ Concurrent Executions         │ 200+ simultaneous                   │
│ System Availability           │ 99.5% uptime                        │
└──────────────────────────────┴─────────────────────────────────────┘
```

### 9.3 Caching Strategy

**Redis Cache Layers**:
```
L1: API Response Cache
- TTL: 60 seconds
- Keys: GET /activities, /templates, /parsers
- Invalidation: On POST/PUT/DELETE operations

L2: Execution Status Cache
- TTL: 30 seconds
- Keys: execution:{id}:status
- Update: Real-time via Celery task
- Purpose: Reduce database load for status queries

L3: Session Cache
- TTL: 24 hours
- Keys: session:{token_hash}
- Purpose: Fast token validation without database hit

L4: Configuration Cache
- TTL: 300 seconds
- Keys: activity:{id}, parser:{id}
- Purpose: Reduce database queries during execution
```

### 9.4 Database Optimization

**Indexing Strategy**:
```sql
-- Activity lookups
CREATE INDEX idx_activities_name ON activities(name);
CREATE INDEX idx_activities_domain ON activities(domain);
CREATE INDEX idx_activities_git_sha ON activities(git_commit_sha);

-- Execution queries
CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_created_at ON executions(created_at DESC);
CREATE INDEX idx_executions_user_id ON executions(user_id);

-- Node results
CREATE INDEX idx_node_results_execution_id ON node_results(execution_id);
CREATE INDEX idx_node_results_status ON node_results(status);

-- JSONB indexes for extracted_data queries
CREATE INDEX idx_node_results_extracted_data ON node_results USING GIN(extracted_data);
CREATE INDEX idx_executions_input_data ON executions USING GIN(input_data);

-- Schedules
CREATE INDEX idx_schedules_next_execution ON schedules(next_execution_at) WHERE active = true;
```

**Query Optimization**:
- Use `EXPLAIN ANALYZE` to identify slow queries
- Batch inserts for node results (100 at a time)
- Pagination with cursor-based navigation (not OFFSET)
- Avoid N+1 queries with SQLAlchemy eager loading
- Use database connection pooling (min: 5, max: 20)

### 9.5 Bottleneck Mitigation

**Common Bottlenecks & Solutions**:
```
1. SSH Connection Overhead
   Solution: Connection pooling, reuse connections across commands

2. Parser Execution Time
   Solution: Compile regex patterns once, cache in memory

3. Database Write Contention
   Solution: Batch writes, use async SQLAlchemy, read replicas

4. Message Broker Saturation
   Solution: Priority queues, message batching, compression

5. API Gateway Overload
   Solution: Response caching, rate limiting, horizontal scaling

6. Large Result Sets
   Solution: Stream results, paginate, compress responses
```

---

## 10. Disaster Recovery

### 10.1 Backup Strategy

**Database Backups**:
```
Frequency: Daily (full) + Continuous WAL archiving
Retention: 30 days online, 1 year archived
Storage: S3/MinIO with versioning enabled
Encryption: AES-256 encryption at rest

Backup Process:
1. pg_dump with --format=custom for compression
2. Upload to S3 with timestamp: backup-YYYY-MM-DD-HH-MM-SS.dump
3. Verify backup integrity with pg_restore --list
4. Test restoration monthly to staging environment

RTO: 1 hour (time to restore from backup)
RPO: 5 minutes (WAL archiving interval)
```

**Configuration Backups**:
```
Git Repository: Primary source of truth (already versioned)
Database Snapshot: Daily export of activities/parsers to JSON
Kubernetes Manifests: Stored in Git, backed up to S3

Backup Script:
- Export activities: SELECT * FROM activities → activities_backup.json
- Export parsers: SELECT * FROM parsers → parsers_backup.json
- Upload to S3 with timestamp
```

**Object Storage Backups**:
```
MinIO to S3 Replication:
- Real-time replication to external S3 bucket
- Cross-region replication for geo-redundancy
- Lifecycle policies: Delete after 90 days
```

### 10.2 High Availability

**Component HA**:
```
API Gateway:
- 3 replicas across 3 availability zones
- Health checks with automatic pod restart
- Rolling updates with zero downtime

Celery Workers:
- Min 2 replicas for redundancy
- Task retry on worker failure
- Work-stealing for load distribution

PostgreSQL:
- Primary-replica setup with automatic failover
- Patroni or Stolon for HA management
- Synchronous replication for zero data loss

RabbitMQ:
- 3-node cluster with mirrored queues
- Automatic partition healing
- Persistent messages survive restarts

Redis:
- Redis Sentinel for automatic failover
- 1 master + 2 replicas
- Cache-aside pattern (tolerate cache loss)
```

### 10.3 Disaster Scenarios & Recovery

**Scenario 1: Database Failure**
```
Symptoms: PostgreSQL pod crash or data corruption
Recovery Steps:
1. Kubernetes auto-restarts failed pod (30 seconds)
2. If restart fails → Failover to read replica (2 minutes)
3. Promote replica to primary
4. Reconfigure application to new primary
5. Restore original primary from backup if needed

Total Downtime: <5 minutes
```

**Scenario 2: RabbitMQ Cluster Failure**
```
Symptoms: All RabbitMQ nodes down
Recovery Steps:
1. Workers cannot receive tasks → queue locally
2. Restore RabbitMQ from persistent volumes (1 minute)
3. Workers reconnect automatically
4. Process queued messages

Total Downtime: <2 minutes (execution delay, no data loss)
```

**Scenario 3: Kubernetes Cluster Failure**
```
Symptoms: Entire cluster unreachable
Recovery Steps:
1. Traffic routed to standby cluster (if multi-cluster setup)
2. Restore database from latest backup to new cluster
3. Restore MinIO data from S3 replication
4. Deploy applications from Git repository
5. Verify smoke tests pass
6. Update DNS to new cluster

Total Downtime: 1-2 hours (depends on multi-cluster setup)
```

**Scenario 4: Data Corruption**
```
Symptoms: Invalid data in database affecting executions
Recovery Steps:
1. Identify corruption time from audit logs
2. Stop write operations to affected tables
3. Restore from backup before corruption time
4. Replay WAL logs from backup point to current
5. Validate data integrity
6. Resume operations

Total Downtime: 30 minutes to 1 hour
```

### 10.4 Runbook Automation

**Automated Recovery**:
- Pod crashes → Kubernetes restarts automatically
- Database failover → Patroni handles automatically
- Worker overload → HPA scales up automatically
- Health check failure → Pod replaced automatically

**Manual Intervention Required**:
- Data corruption detection
- Security incidents
- Multi-cluster failover
- Backup restoration testing

---

## Document Revision History

| Version | Date       | Author | Changes                          |
|---------|------------|--------|----------------------------------|
| 1.0     | 2026-06-09 | System | Initial HLD document creation    |

---

## Appendices

### A. Acronyms and Terminology

- **HPA**: Horizontal Pod Autoscaler
- **KEDA**: Kubernetes Event-Driven Autoscaling
- **RBAC**: Role-Based Access Control
- **RTO**: Recovery Time Objective
- **RPO**: Recovery Point Objective
- **WAL**: Write-Ahead Logging (PostgreSQL)
- **mTLS**: Mutual TLS (bidirectional authentication)
- **OSS**: Operations Support System (jump host for device access)
- **State_Data_Map**: In-memory dictionary storing execution state variables
- **node_pars**: Node parameters dictionary (IP, credentials, custom vars)

### B. References

- Design Document: `.kiro/specs/telecom-automation-platform/design.md`
- Requirements: `.kiro/specs/telecom-automation-platform/requirements.md`
- Implementation Tasks: `.kiro/specs/telecom-automation-platform/tasks.md`
- Legacy System Understanding: `LEGACY_SYSTEM_UNDERSTANDING.md`
- Solution Approach Guide: `DOCS/10_SOLUTION_APPROACH_GUIDE.md`
