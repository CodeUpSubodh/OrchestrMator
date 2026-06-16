# Learning-Focused Implementation Plan

## Philosophy: Learn by Building, Not by Copying

This plan is designed to enhance your technical skills through hands-on learning. Each phase includes:
- **Conceptual Understanding**: Why we're doing it this way
- **Technology Context**: Multiple approaches and trade-offs
- **Step-by-Step Learning**: Build incrementally with explanations
- **Decision Points**: Where you make architectural choices
- **Reference Resources**: Links to learn more

---

## PHASE 0: LEARNING FOUNDATION (Week 1)

### Goal: Understand modern architecture patterns before coding

#### 0.1 System Design Learning
**Topics to Study**:
- Microservices vs Monolith
- Event-driven architecture
- Message queues (RabbitMQ vs Kafka vs Redis)
- API design (REST vs GraphQL vs gRPC)

**Practical Exercise**:
- Draw architecture diagram for your system
- Identify service boundaries
- Map data flows
- Document decision rationale

**Resources**:
- "Designing Data-Intensive Applications" (Martin Kleppmann)
- System Design Primer: https://github.com/donnemartin/system-design-primer

#### 0.2 Technology Stack Research
**Decision Points**:

1. **Backend Framework**: FastAPI vs Flask vs Django
   - FastAPI: Modern, async, auto-docs, type hints
   - Flask: Simple, flexible, mature ecosystem
   - Django: Batteries-included, ORM, admin panel
   - **Recommendation**: FastAPI for learning modern Python + performance

2. **Workflow Engine**: Temporal vs Airflow vs Celery vs None
   - Temporal: Distributed, reliable, complex setup
   - Airflow: DAG-based, UI, batch-oriented
   - Celery: Simple, mature, just task queue
   - None: Start simple, add later
   - **Recommendation**: Start with Celery, migrate to Temporal later

3. **Database**: PostgreSQL vs MySQL vs MongoDB
   - PostgreSQL: JSONB, full-featured, ACID
   - **Recommendation**: PostgreSQL for structured + semi-structured data

4. **Message Broker**: RabbitMQ vs Kafka vs Redis
   - RabbitMQ: Task queues, simpler setup
   - Kafka: Event streaming, higher throughput
   - Redis: Simplest, less durable
   - **Recommendation**: RabbitMQ for task queue pattern

**Exercise**: Write a document defending your technology choices

---

## PHASE 1: MINIMAL VIABLE BACKEND (Weeks 2-3)

### Goal: Build a working API that can trigger one automation

#### Learning Objectives:
- FastAPI basics and async programming
- Pydantic models and validation
- Database design with SQLAlchemy
- Docker containerization
- API testing with pytest

### Step 1.1: Project Structure Setup (Days 1-2)

**Concept**: Monorepo structure for microservices

```
telecom-automation-platform/
├── backend/
│   ├── api-gateway/          # REST API
│   ├── workflow-engine/      # Celery workers (future)
│   ├── shared/               # Common code
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── utils/            # Helpers
│   └── tests/
├── frontend/                 # React app (future)
├── infrastructure/
│   ├── docker/
│   └── kubernetes/          # Future
└── docs/
```

**Why this structure?**
- Shared code reused across services
- Independent service deployment
- Clear separation of concerns

**Exercise**:
1. Create directory structure
2. Initialize Python project with Poetry or pip
3. Set up .gitignore
4. Write README explaining structure

**Learning Resources**:
- FastAPI project structure: https://fastapi.tiangolo.com/tutorial/bigger-applications/
- Python packaging: https://packaging.python.org/

### Step 1.2: Database Models (Days 3-4)

**Concept**: Domain-driven design for data modeling

**Start Simple - 4 Core Tables**:


```python
# backend/shared/models/activity.py
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB

class Activity(Base):
    """Represents an automation activity definition"""
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    domain = Column(String(50))  # ran, core, pbn, etc.
    description = Column(Text)
    config = Column(JSONB)  # YAML config stored as JSON
    created_at = Column(DateTime)
    
# Why JSONB for config?
# - Flexible schema as we iterate
# - Queryable in PostgreSQL
# - Can validate with Pydantic before storing
```

**Learning Exercise**:
1. Design remaining tables: `executions`, `node_results`, `users`
2. Create SQLAlchemy models
3. Write Alembic migrations
4. Seed database with sample data

**Questions to Answer**:
- Why SQLAlchemy ORM vs raw SQL?
- What are migrations and why use them?
- What's the difference between Column types?
- When to use ForeignKey vs manual references?

**Resources**:
- SQLAlchemy tutorial: https://docs.sqlalchemy.org/en/14/tutorial/
- Alembic migrations: https://alembic.sqlalchemy.org/en/latest/tutorial.html

### Step 1.3: Pydantic Schemas (Days 4-5)

**Concept**: Input validation and serialization

```python
# backend/shared/schemas/activity.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional

class ActivityCreate(BaseModel):
    """Schema for creating new activity"""
    name: str = Field(..., min_length=1, max_length=200)
    domain: str = Field(..., regex="^(ran|core|pbn|paco|txn)$")
    description: Optional[str]
    config: dict
    
    @validator('config')
    def validate_config(cls, v):
        # Custom validation logic
        required_fields = ['commands']
        if 'commands' not in v:
            raise ValueError('config must have commands')
        return v

class ActivityResponse(BaseModel):
    """Schema for API responses"""
    id: int
    name: str
    domain: str
    
    class Config:
        orm_mode = True  # Allow conversion from SQLAlchemy models
```

**Why Pydantic?**
- Automatic request validation
- Type safety
- Auto-generated API docs
- Serialization/deserialization

**Exercise**:
1. Create schemas for all models
2. Write validators for business rules
3. Test schemas with pytest

### Step 1.4: FastAPI Endpoints (Days 5-7)

**Concept**: RESTful API design

```python
# backend/api-gateway/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

app = FastAPI(
    title="Telecom Automation API",
    version="1.0.0",
    docs_url="/docs"
)

@app.post("/api/v1/activities", response_model=ActivityResponse)
async def create_activity(
    activity: ActivityCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new automation activity
    
    This endpoint:
    1. Validates input using Pydantic
    2. Checks for duplicate names
    3. Stores in database
    4. Returns created activity
    """
    # Check duplicate
    existing = db.query(Activity).filter(
        Activity.name == activity.name
    ).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Activity '{activity.name}' already exists"
        )
    
    # Create
    db_activity = Activity(**activity.dict())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    return db_activity
```

**Learning Points**:
- Dependency injection with `Depends()`
- HTTP status codes (200, 201, 400, 404, 409, 500)
- Error handling with HTTPException
- Database session management
- Async vs sync endpoints

**Exercise**:
1. Implement CRUD endpoints for activities
2. Add pagination to list endpoint
3. Implement filtering and search
4. Write OpenAPI documentation
5. Test with curl/Postman

**Questions to Research**:
- When to use async def vs def?
- How does FastAPI handle concurrency?
- What's the difference between Path, Query, Body parameters?

### Step 1.5: Docker Setup (Days 7-8)

**Concept**: Containerization for consistency

```dockerfile
# backend/api-gateway/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: ./backend/api-gateway
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://user:pass@db:5432/automation
    volumes:
      - ./backend/api-gateway:/app
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: automation
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

**Why Docker?**
- Consistent environment across dev/staging/prod
- Easy dependency management
- Isolated services
- Simple local development setup

**Exercise**:
1. Write Dockerfiles for each service
2. Create docker-compose.yml
3. Run `docker-compose up`
4. Verify API accessible at http://localhost:8000/docs
5. Test database connectivity

**Learning**:
- Dockerfile best practices (layer caching, multi-stage builds)
- Docker networking
- Volume management
- Health checks

---

## PHASE 2: EXECUTION ENGINE (Weeks 4-5)

### Goal: Execute a simple automation end-to-end

#### Learning Objectives:
- SSH connection management
- Command execution and output capture
- State management
- Error handling and retries

### Step 2.1: SSH Client Wrapper (Days 9-10)

**Concept**: Abstract SSH complexity

```python
# backend/shared/utils/ssh_client.py
import paramiko
from typing import Tuple

class SSHClient:
    """Manages SSH connections to network devices"""
    
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.client = None
        self.shell = None
    
    def connect(self, timeout: int = 10) -> None:
        """Establish SSH connection"""
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(
            hostname=self.host,
            username=self.username,
            password=self.password,
            timeout=timeout
        )
        self.shell = self.client.invoke_shell()
    
    def execute_command(
        self, 
        command: str, 
        expect_prompt: str = "#",
        timeout: int = 30
    ) -> Tuple[str, bool]:
        """
        Execute command and wait for prompt
        
        Returns:
            (output, success)
        """
        # Implementation details...
```

**Why abstract SSH?**
- Reusable across different vendors
- Centralized error handling
- Easy to mock for testing
- Can add retry logic in one place

**Exercise**:
1. Implement SSHClient class
2. Add prompt detection with regex
3. Implement timeout handling
4. Write unit tests with mocking
5. Test against real device (or simulator)

**Questions**:
- How does paramiko handle SSH keys vs passwords?
- What's the difference between exec_command() and invoke_shell()?
- How to handle interactive prompts?

### Step 2.2: Command Executor Service (Days 11-12)

**Concept**: Stateful command execution

```python
# backend/workflow-engine/executor.py
class CommandExecutor:
    """Executes command sequences on nodes"""
    
    def __init__(self, node_config: dict):
        self.node_ip = node_config['node_ip']
        self.credentials = node_config['credentials']
        self.state_data = {}  # State_Data_Map
        self.ssh = None
    
    async def execute_sequence(
        self, 
        commands: List[CommandConfig]
    ) -> ExecutionResult:
        """Execute full command sequence"""
        
        self.ssh = SSHClient(self.node_ip, ...)
        self.ssh.connect()
        
        results = []
        for cmd in commands:
            # Substitute variables
            resolved_cmd = self.resolve_variables(cmd.template)
            
            # Execute
            output, success = self.ssh.execute_command(
                resolved_cmd,
                expect_prompt=cmd.expect_prompt
            )
            
            # Parse
            if cmd.parser:
                parsed = self.apply_parser(cmd.parser, output)
                self.state_data.update(parsed)
            
            results.append({
                'command': resolved_cmd,
                'output': output,
                'success': success
            })
            
            # Control flow
            if not success and cmd.on_failure:
                # Jump to failure handler
                pass
        
        return ExecutionResult(results)
    
    def resolve_variables(self, template: str) -> str:
        """Replace <<<var>>> with values from state_data"""
        import re
        pattern = r'<<<(\w+)>>>'
        
        def replacer(match):
            var_name = match.group(1)
            return self.state_data.get(var_name, match.group(0))
        
        return re.sub(pattern, replacer, template)
```

**Learning Points**:
- State management patterns
- Variable substitution
- Error propagation
- Control flow implementation

**Exercise**:
1. Implement CommandExecutor
2. Add logging at each step
3. Implement control flow (GOTO logic)
4. Write integration tests
5. Test with mock SSH

---

## PHASE 3: PARSER FRAMEWORK (Week 6)

### Goal: Build flexible parsing system

#### Learning Objectives:
- Strategy pattern for parsers
- Regular expressions mastery
- Dynamic code loading
- Testing complex logic

### Step 3.1: Parser Base Class (Days 13-14)

**Concept**: Template method pattern

```python
# backend/shared/parsers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseParser(ABC):
    """Base class for all parsers"""
    
    def __init__(self, command_pattern: str = None):
        self.command_pattern = command_pattern
    
    @abstractmethod
    def parse(self, output: str) -> ParseResult:
        """
        Parse command output
        
        Args:
            output: Raw command output
        
        Returns:
            ParseResult with extracted data
        """
        pass
    
    def validate_output(self, output: str) -> bool:
        """Check if output is valid before parsing"""
        return len(output) > 0
    
    def post_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up extracted data"""
        return data

class ParseResult:
    """Result of parsing operation"""
    def __init__(
        self, 
        success: bool,
        extracted_data: Dict[str, Any],
        errors: List[str] = None
    ):
        self.success = success
        self.data = extracted_data
        self.errors = errors or []
```

**Why inheritance here?**
- Common validation logic
- Consistent interface
- Easy to test
- Enforces contract

**Exercise**:
1. Implement BaseParser
2. Create RegexParser subclass
3. Create JSONParser subclass
4. Write parser tests

### Step 3.2: Parser Registry (Days 14-15)

**Concept**: Registry pattern for dynamic loading

```python
# backend/shared/parsers/registry.py
class ParserRegistry:
    """Registry for all available parsers"""
    
    _parsers = {}
    
    @classmethod
    def register(cls, name: str):
        """Decorator to register parser"""
        def decorator(parser_class):
            cls._parsers[name] = parser_class
            return parser_class
        return decorator
    
    @classmethod
    def get_parser(cls, name: str) -> BaseParser:
        """Get parser instance by name"""
        if name not in cls._parsers:
            raise ValueError(f"Parser '{name}' not registered")
        return cls._parsers[name]()

# Usage:
@ParserRegistry.register("parse_interface_status")
class InterfaceStatusParser(BaseParser):
    def parse(self, output: str) -> ParseResult:
        # Implementation
        pass
```

**Learning**:
- Decorator pattern
- Class registration
- Plugin architecture

This builds foundation for visual parser builder later!

---

## DECISION CHECKPOINT: After Phase 3

At this point, you have:
✅ Working API
✅ Database models
✅ SSH execution
✅ Parser framework

**Now decide**:
1. Build GUI first (Visual Parser Builder)?
2. Add more backend features (scheduling, parallel execution)?
3. Focus on DevOps (CI/CD, Kubernetes)?

**Recommendation**: Build GUI parser builder next - it's high value and teaches frontend integration.

---

## Next Document Will Cover:
- Phase 4: Visual Parser Builder (React + Backend integration)
- Phase 5: Activity Builder GUI
- Phase 6: Production Deployment
- Phase 7: Advanced Features

Would you like me to continue with detailed plans for these phases?