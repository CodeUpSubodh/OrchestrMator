# Solution Approaches & Technical Decision Making

## Core Philosophy: Multiple Valid Solutions

For each problem, there are multiple valid approaches. This guide explains:
- **What** each approach does
- **Why** you might choose it
- **When** it's the right fit
- **Trade-offs** to consider

---

## DECISION 1: Microservices vs Monolith

### Problem Context
Legacy system is a monolithic Python application. Should new system be microservices?

### Approach A: Start Monolithic (Recommended for Learning)
**What**: Single FastAPI application with modular internal structure

**Why Choose This**:
- Faster initial development
- Simpler debugging (one process)
- No distributed system complexity
- Easier to understand data flow
- Can split into microservices later

**When To Choose**:
- Team < 10 developers
- < 1000 req/second expected
- Learning distributed systems
- Want to ship MVP fast

**Implementation**:
```python
# All in one app, but modular
api-gateway/
  main.py
  routers/
    activities.py     # Activity endpoints
    executions.py     # Execution endpoints
  services/
    executor.py       # Execution logic
    parser.py         # Parser logic
  models/             # Database models
```

**Pros**:
- Simple deployment (one container)
- Easy transaction management
- Fast internal communication
- Simplified testing

**Cons**:
- All code in one repo
- Can't scale components independently
- One bug can crash everything
- Harder to use different languages

---

### Approach B: Microservices from Start
**What**: Separate services communicating via API/message queue

**Why Choose This**:
- Need independent scaling
- Different teams own different services
- Want technology diversity
- Learning microservices architecture

**When To Choose**:
- Large team (>10 developers)
- High scale requirements
- Different performance profiles per service
- Already know microservices patterns

**Implementation**:
```
api-gateway/        # FastAPI - handles HTTP
workflow-engine/    # Temporal - orchestrates
executor-service/   # Python - executes commands
parser-service/     # Python - parses outputs
report-service/     # Python - generates reports
```

**Pros**:
- Scale services independently
- Isolate failures
- Technology freedom per service
- Parallel team development

**Cons**:
- Complex networking
- Distributed debugging hard
- Data consistency challenges
- More operational overhead

---

### **Recommendation**: Monolith First Strategy

**Phase 1 (Months 0-6)**: Build as modular monolith
- Faster MVP
- Learn domain
- Iterate quickly

**Phase 2 (Months 6-12)**: Extract services gradually
- Extract high-load components (executor)
- Extract components that need different scaling
- Use strangler pattern

**Why This Works**:
- Less risky
- Learn what needs to be separate
- Don't pay microservices tax early
- Can always split later (but merging is hard)

---

## DECISION 2: Message Queue - RabbitMQ vs Kafka vs Redis

### Problem Context
Need async task processing for node executions. Which message broker?

### Approach A: RabbitMQ (Recommended)
**What**: Traditional message broker with queues and exchanges

**Why Choose This**:
- Task queue pattern (perfect for jobs)
- Simple setup
- Good for request-response
- Mature Python clients (Celery)
- Built-in UI for monitoring

**When To Choose**:
- Processing jobs/tasks
- Need acknowledgments
- Want simple mental model
- Using Celery workers

**Use Case Fit**: ✅ Perfect
- Automation requests are tasks
- Need task retries
- Want task acknowledgment
- Celery integrates perfectly

**Implementation**:
```python
# Publisher
from celery import Celery

app = Celery('tasks', broker='amqp://rabbitmq')

@app.task
def execute_automation(activity_id, node_ip):
    # Execute automation
    pass

# Consumer
execute_automation.delay(activity_id='123', node_ip='10.1.1.1')
```

---

### Approach B: Kafka
**What**: Distributed event streaming platform

**Why Choose This**:
- Event sourcing architecture
- High throughput (millions/sec)
- Event replay capability
- Multi-consumer support

**When To Choose**:
- Event-driven architecture
- Need event history
- Very high scale (>10k messages/sec)
- Multiple services consume same events

**Use Case Fit**: ❌ Overkill (initially)
- More complex than needed
- Automation requests aren't "events"
- Don't need replay initially
- Higher operational complexity

**When To Add Kafka Later**:
- For audit log streaming
- Real-time metrics pipeline
- If scale exceeds RabbitMQ

---

### Approach C: Redis Pub/Sub
**What**: In-memory data store with pub/sub

**Why Choose This**:
- Simplest setup
- Very fast
- Already using for caching

**When To Choose**:
- Low message durability requirements
- Simple use case
- Using Redis anyway

**Use Case Fit**: ❌ Not Recommended
- Less durable (can lose messages)
- No dead letter queue
- No message acknowledgment
- Better as cache, not queue

---

### **Recommendation**: RabbitMQ + Celery

**Why**:
- Built for task distribution
- Celery provides retries, scheduling, monitoring
- Can upgrade to Kafka later if needed
- Industry standard for this pattern

**Migration Path**:
- Start: RabbitMQ + Celery
- Later: Add Kafka for event streaming (audit logs, metrics)
- Keep both: RabbitMQ for tasks, Kafka for events

---

## DECISION 3: Workflow Orchestration

### Problem Context
Need to coordinate multi-step automation workflows. How to manage?

### Approach A: No Orchestrator (Simple State Machine)
**What**: Execute commands sequentially in code

**Why Choose This**:
- Simplest to understand
- No external dependencies
- Fast to build

**Implementation**:
```python
class SimpleOrchestrator:
    async def execute(self, commands):
        state = {}
        for cmd in commands:
            output = await self.ssh.execute(cmd)
            state.update(self.parse(output))
            if not output.success:
                break
        return state
```

**Pros**:
- Easy to debug
- No learning curve
- Works for simple workflows

**Cons**:
- No retry on failure
- Can't resume if crashes
- No visibility into progress
- Hard to handle complex workflows

**When To Choose**: MVP only

---

### Approach B: Celery Workflows
**What**: Celery's canvas (chain, group, chord)

**Why Choose This**:
- Already using Celery
- Built-in primitives for workflows
- No new infrastructure

**Implementation**:
```python
from celery import chain, group

# Sequential execution
workflow = chain(
    ssh_connect.s(node_ip),
    execute_command.s("show version"),
    parse_output.s(),
    execute_command.s("show interface")
)

# Parallel execution
parallel = group(
    execute_on_node.s(node1),
    execute_on_node.s(node2),
    execute_on_node.s(node3)
)
```

**Pros**:
- No new tools
- Retries built-in
- Task monitoring

**Cons**:
- Limited workflow patterns
- Hard to model complex logic
- No visual workflow builder
- State management manual

**When To Choose**: Phases 1-2 (first 6 months)

---

### Approach C: Temporal Workflow Engine
**What**: Durable workflow execution platform

**Why Choose This**:
- Workflows as code
- Auto-retry and recovery
- Built-in versioning
- Excellent visibility

**Implementation**:
```python
import temporal

@temporal.workflow.defn
class AutomationWorkflow:
    @temporal.workflow.run
    async def run(self, nodes):
        results = []
        for node in nodes:
            result = await temporal.workflow.execute_activity(
                execute_node,
                node,
                start_to_close_timeout=timedelta(minutes=30)
            )
            results.append(result)
        return results
```

**Pros**:
- Workflows survive process restarts
- Built-in retry logic
- Excellent debugging
- Version multiple workflow versions

**Cons**:
- Steep learning curve
- More infrastructure (Temporal server)
- Overkill for simple workflows

**When To Choose**: Phase 3+ (after 6 months)

---

### **Recommendation**: Phased Approach

**Phase 1 (Months 0-3)**: Simple state machine
- Learn the domain
- Prove the concept
- Fast iteration

**Phase 2 (Months 3-9)**: Celery workflows
- Add retry logic
- Handle parallel execution
- Production-ready

**Phase 3 (Months 9+)**: Evaluate Temporal
- If workflows become complex
- If need better visibility
- If scale demands it

---

## DECISION 4: Configuration Format

### Problem Context
Replace CSV activity configs. What format?

### Approach A: YAML (Recommended)
**What**: Human-readable data serialization

**Example**:
```yaml
activity:
  name: nokia-syslog-precheck
  domain: pbn

commands:
  - id: 1
    template: "ssh <<<node_user>>>@<<<node_ip>>>"
    parsers: [parse_ssh_login]
    on_success: 2
    on_failure: 99
    
  - id: 2
    template: "<<<node_pass>>>"
    mask: true
    on_success: 3
```

**Pros**:
- Very readable
- Comments supported
- Good Git diffs
- Python libraries mature

**Cons**:
- Whitespace-sensitive
- Can be verbose
- No schema enforcement (need separate validation)

---

### Approach B: JSON
**Example**:
```json
{
  "activity": {
    "name": "nokia-syslog-precheck",
    "commands": [
      {
        "id": 1,
        "template": "ssh <<<node_user>>>@<<<node_ip>>>",
        "parsers": ["parse_ssh_login"]
      }
    ]
  }
}
```

**Pros**:
- Native JavaScript support
- Schema with JSON Schema
- Strict parsing

**Cons**:
- No comments
- Less readable
- Verbose (quotes everywhere)

---

### Approach C: TOML
**Example**:
```toml
[activity]
name = "nokia-syslog-precheck"
domain = "pbn"

[[commands]]
id = 1
template = "ssh <<<node_user>>>@<<<node_ip>>>"
parsers = ["parse_ssh_login"]
```

**Pros**:
- Very clean
- Comments supported
- Type-safe

**Cons**:
- Less common
- Harder for nested structures

---

### **Recommendation**: YAML + JSON Schema

**Why**:
- Best readability for humans
- JSON Schema provides validation
- Industry standard for configs (Kubernetes, Docker Compose, CI/CD)
- Easy to convert to JSON for API

**Validation**:
```python
import yaml
import jsonschema

# Load YAML
with open('activity.yaml') as f:
    config = yaml.safe_load(f)

# Validate
schema = {...}  # JSON Schema
jsonschema.validate(config, schema)
```

---

## Summary Decision Matrix

| Decision | Phase 1 (MVP) | Phase 2 (Production) | Phase 3 (Scale) |
|----------|---------------|---------------------|-----------------|
| Architecture | Modular Monolith | Monolith | Extract Microservices |
| Message Queue | RabbitMQ | RabbitMQ | RabbitMQ + Kafka |
| Workflow | Simple State Machine | Celery | Temporal |
| Config Format | YAML | YAML | YAML |
| Database | PostgreSQL | PostgreSQL | PostgreSQL + TimescaleDB |
| Deployment | Docker Compose | Kubernetes | Kubernetes + Service Mesh |

**Key Principle**: Start simple, add complexity only when needed.

Next: Detailed implementation guide for each phase!