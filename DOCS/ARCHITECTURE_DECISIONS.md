# Architecture Decision Record (ADR)

## ADR-001: Multi-Entry Point Architecture

**Status:** Accepted  
**Date:** 2026-06-22  
**Decision Makers:** Development Team

---

### Context

OrchestrMator is a complex system with multiple concerns:
- REST API for external clients
- Background task processing (Celery workers)
- Scheduled job execution (Celery beat)
- Potential future services (monitoring, reporting)

We need to decide between:
1. **Monolithic single entry point** - One main.py for everything
2. **Multiple entry points** - Separate main.py for each service

---

### Decision

**We will use multiple entry points with a service orchestrator.**

```
backend/
├── main.py                      # Service Orchestrator (CLI)
├── api_gateway/main.py          # FastAPI REST API
├── workflow_engine/main.py      # Celery Worker
└── scheduler/main.py            # Celery Beat
```

---

### Rationale

**Advantages:**
1. **Independent Scaling**
   - Scale API servers separately from workers
   - Run 10 API instances + 20 worker instances

2. **Service Isolation**
   - API crash doesn't affect workers
   - Worker bugs don't impact API availability

3. **Development Flexibility**
   - Work on API without running workers
   - Test workers without API running
   - Faster development iteration

4. **Deployment Options**
   - Deploy services as separate containers
   - Use Kubernetes deployments per service
   - Different resource limits per service

5. **Clear Separation of Concerns**
   - API handles HTTP requests
   - Workers handle background tasks
   - Scheduler triggers recurring jobs

**Trade-offs:**
1. Slightly more complex than single entry point
2. Need orchestrator or container orchestration
3. More configuration in production

---

### Implementation

#### Service Orchestrator: `backend/main.py`

**Purpose:** CLI tool to launch any service

**Usage:**
```bash
# Development
python -m backend.main api              # API only
python -m backend.main worker           # Worker only
python -m backend.main all              # All services

# Production (direct commands)
uvicorn backend.api_gateway.main:app    # API
celery -A backend.workflow_engine worker # Worker
```

#### API Gateway: `backend/api_gateway/main.py`

**Purpose:** FastAPI application serving REST API

**Responsibilities:**
- HTTP request handling
- Authentication/authorization
- Request validation
- Database CRUD operations
- Publishing messages to task queue

#### Worker: `backend/workflow_engine/main.py`

**Purpose:** Celery worker consuming tasks from queue

**Responsibilities:**
- Execute automation workflows
- SSH command execution
- Result processing and storage
- Error handling and retries

#### Scheduler: `backend/scheduler/main.py`

**Purpose:** Celery beat triggering scheduled tasks

**Responsibilities:**
- Poll schedule table
- Trigger automations at specified times
- Handle cron expressions

---

### Consequences

#### Positive

✅ Each service can be scaled independently  
✅ Services can be deployed/restarted independently  
✅ Clearer code organization  
✅ Easier to add new services  
✅ Better resource utilization in production  

#### Negative

⚠️ More files to manage  
⚠️ Need to understand which service does what  
⚠️ Slightly more complex local development setup  

#### Mitigation

- Provide clear documentation (this file)
- Service orchestrator simplifies local development
- Makefile commands for common operations
- Docker Compose runs all services together

---

### Comparison with Alternatives

#### Alternative 1: Single Entry Point

```
backend/main.py    # Everything in one file
```

**Rejected because:**
- Can't scale components independently
- Mixing concerns (HTTP + background tasks)
- Harder to test in isolation

#### Alternative 2: Microservices per Module

```
backend/auth_service/main.py
backend/activity_service/main.py
backend/execution_service/main.py
backend/workflow_service/main.py
```

**Rejected because:**
- Over-engineering for current scale
- Too much inter-service communication overhead
- More complex to develop and debug
- Can refactor to this later if needed

---

### How to Add a New Service

1. Create service directory: `backend/new_service/`
2. Create entry point: `backend/new_service/main.py`
3. Update orchestrator: `backend/main.py`
4. Add to Makefile commands
5. Add to docker-compose.yml (if applicable)
6. Document in this ADR

---

### Related Documents

- [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md) - Full development plan
- [PHASE_2_API_GATEWAY_DETAILED.md](./PHASE_2_API_GATEWAY_DETAILED.md) - API Gateway specs

---

### Review Schedule

**Next Review:** After Phase 7 (Scheduler implementation)  
**Review Trigger:** If services become too coupled or scaling issues arise
