# Low-Level Design (LLD): Cloud-Native Telecom Automation Platform

## Document Information
- **Version**: 1.0
- **Date**: June 9, 2026
- **Purpose**: Define detailed component designs, class structures, interfaces, algorithms, and data models

## Table of Contents
1. [Database Schema Design](#database-schema-design)
2. [API Endpoint Specifications](#api-endpoint-specifications)
3. [Core Component Designs](#core-component-designs)
4. [Algorithm Designs](#algorithm-designs)
5. [Message Queue Design](#message-queue-design)
6. [Parser Framework Design](#parser-framework-design)
7. [Frontend Component Design](#frontend-component-design)
8. [Configuration Schema](#configuration-schema)

---

## 1. Database Schema Design

### 1.1 Entity Relationship Diagram (ERD)

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│     users       │         │   activities    │         │   parsers       │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)         │         │ id (PK)         │
│ email           │         │ name (UNIQUE)   │         │ name            │
│ password_hash   │◄───┐    │ domain          │         │ domain          │
│ role            │    │    │ description     │    ┌───►│ parser_type     │
│ is_active       │    │    │ config (JSONB)  │    │    │ code (TEXT)     │
│ created_at      │    │    │ version         │    │    │ created_by (FK) │
└─────────────────┘    │    │ git_commit_sha  │    │    │ created_at      │
                       │    │ created_by (FK) │────┘    └─────────────────┘
                       │    │ created_at      │
                       │    └─────────────────┘
                       │              │
                       │              │ 1:N
                       │              ▼
                       │    ┌─────────────────┐
                       │    │   executions    │
                       │    ├─────────────────┤
                       │    │ id (PK)         │
                       └────┤ user_id (FK)    │
                            │ activity_id (FK)│────┐
                            │ cr_id           │    │
                            │ status          │    │
                            │ execution_mode  │    │
                            │ input_data (JSONB)  │
                            │ max_parallelism │    │
                            │ created_at      │    │
                            │ started_at      │    │
                            │ completed_at    │    │
                            └─────────────────┘    │
                                     │             │
                                     │ 1:N         │
                                     ▼             │
                            ┌─────────────────┐   │
                            │  node_results   │   │
                            ├─────────────────┤   │
                            │ id (PK)         │   │
                            │ execution_id(FK)│───┘
                            │ node_name       │
                            │ node_ip         │
                            │ status          │
                            │ extracted_data  │
                            │   (JSONB)       │
                            │ state_data      │
                            │   (JSONB)       │
                            │ log_file_path   │
                            │ error_message   │
                            │ started_at      │
                            │ completed_at    │
                            └─────────────────┘

┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   schedules     │         │  command_results │         │  audit_logs     │
├─────────────────┤         ├──────────────────┤         ├─────────────────┤
│ id (PK)         │         │ id (PK)          │         │ id (PK)         │
│ activity_id(FK) │         │ node_result_id   │         │ user_id (FK)    │
│ user_id (FK)    │         │   (FK)           │         │ action          │
│ cron_expression │         │ command_id       │         │ resource_type   │
│ input_data(JSON)│         │ command_text     │         │ resource_id     │
│ next_execution  │         │ output (TEXT)    │         │ ip_address      │
│ is_recurring    │         │ status           │         │ user_agent      │
│ active          │         │ execution_time_ms│         │ success         │
│ created_at      │         │ created_at       │         │ details (JSONB) │
└─────────────────┘         └──────────────────┘         │ timestamp       │
                                                          └─────────────────┘

┌──────────────────┐
│  templates       │
├──────────────────┤
│ id (PK)          │
│ vendor           │
│ device_type      │
│ command_text     │
│ description      │
│ use_case         │
│ tags (ARRAY)     │
│ contributed_by   │
│ is_approved      │
│ popularity_score │
│ created_at       │
└──────────────────┘
       │ 1:N
       ▼
┌──────────────────┐
│ example_outputs  │
├──────────────────┤
│ id (PK)          │
│ template_id (FK) │
│ output_text      │
│ output_type      │
│ created_at       │
└──────────────────┘
```

### 1.2 Detailed Table Schemas

#### users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('admin', 'engineer', 'viewer')),
    is_active BOOLEAN DEFAULT true,
    last_login_at TIMESTAMP,
    failed_login_attempts INT DEFAULT 0,
    account_locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### activities
```sql
CREATE TABLE activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    domain VARCHAR(50) NOT NULL CHECK (domain IN ('ran', 'core', 'pbn', 'paco', 'txn', 'core2')),
    description TEXT,
    config JSONB NOT NULL,  -- Full activity configuration
    version INT DEFAULT 1,
    git_commit_sha VARCHAR(40),
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT config_not_empty CHECK (jsonb_typeof(config) = 'object')
);

CREATE INDEX idx_activities_name ON activities(name);
CREATE INDEX idx_activities_domain ON activities(domain);
CREATE INDEX idx_activities_git_sha ON activities(git_commit_sha);
CREATE INDEX idx_activities_active ON activities(is_active) WHERE is_active = true;

-- JSONB indexes for config queries
CREATE INDEX idx_activities_config_gin ON activities USING GIN(config);
```

**config JSONB Structure**:
```json
{
  "activity": {
    "name": "Nokia_MPBN_Precheck",
    "domain": "pbn",
    "description": "Pre-check for Nokia MPBN nodes"
  },
  "execution": {
    "mode": "parallel",
    "max_parallelism": 50,
    "timeout_seconds": 600,
    "failure_policy": "continue",
    "jump_host": {
      "use_jump_host": true,
      "oss_ip": "<<<oss_ip>>>",
      "oss_user": "<<<oss_user>>>",
      "oss_password": "<<<oss_password>>>"
    }
  },
  "commands": [
    {
      "command_id": 1,
      "template": "show version",
      "expect_prompt": "#",
      "timeout": 30,
      "parsers": ["nokia_version_parser"],
      "on_success": 2,
      "on_failure": 0
    }
  ],
  "additional_module": {
    "enabled": true,
    "modules": ["email_notification", "csv_merger"]
  }
}
```

#### executions
```sql
CREATE TABLE executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) NOT NULL,
    activity_id UUID REFERENCES activities(id) NOT NULL,
    cr_id VARCHAR(50),  -- Change Request ID
    status VARCHAR(50) NOT NULL DEFAULT 'queued' 
        CHECK (status IN ('queued', 'running', 'completed', 'failed', 'cancelled')),
    execution_mode VARCHAR(20) NOT NULL 
        CHECK (execution_mode IN ('sequential', 'parallel', 'batch')),
    input_data JSONB NOT NULL,  -- Node list with parameters
    max_parallelism INT DEFAULT 10,
    total_nodes INT,
    successful_nodes INT DEFAULT 0,
    failed_nodes INT DEFAULT 0,
    output_file_path VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    CONSTRAINT valid_parallelism CHECK (max_parallelism BETWEEN 1 AND 200)
);

CREATE INDEX idx_executions_status ON executions(status);
CREATE INDEX idx_executions_user_id ON executions(user_id);
CREATE INDEX idx_executions_activity_id ON executions(activity_id);
CREATE INDEX idx_executions_created_at ON executions(created_at DESC);
CREATE INDEX idx_executions_cr_id ON executions(cr_id);

-- JSONB index for input_data queries
CREATE INDEX idx_executions_input_data_gin ON executions USING GIN(input_data);
```

**input_data JSONB Structure**:
```json
{
  "nodes": [
    {
      "node_name": "NOKIA_NODE_001",
      "node_ip": "10.20.30.40",
      "node_user": "admin",
      "node_password": "encrypted_password",
      "custom_field_1": "value1",
      "custom_field_2": "value2"
    }
  ]
}
```

#### node_results
```sql
CREATE TABLE node_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES executions(id) ON DELETE CASCADE NOT NULL,
    node_name VARCHAR(255) NOT NULL,
    node_ip VARCHAR(45) NOT NULL,  -- Supports IPv4 and IPv6
    status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    extracted_data JSONB,  -- Parser outputs for Output_Sheet
    state_data JSONB,  -- State_Data_Map for variable resolution
    log_file_path VARCHAR(500),  -- MinIO path to full logs
    error_message TEXT,
    commands_executed INT DEFAULT 0,
    commands_successful INT DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(execution_id, node_name)
);

CREATE INDEX idx_node_results_execution_id ON node_results(execution_id);
CREATE INDEX idx_node_results_status ON node_results(status);
CREATE INDEX idx_node_results_node_name ON node_results(node_name);

-- JSONB indexes for data queries
CREATE INDEX idx_node_results_extracted_data_gin ON node_results USING GIN(extracted_data);
CREATE INDEX idx_node_results_state_data_gin ON node_results USING GIN(state_data);
```

**extracted_data JSONB Structure** (for output sheet):
```json
{
  "version": "7.0R1",
  "uptime": "45 days",
  "interfaces": [
    {"name": "eth0", "status": "up", "ip": "10.1.1.1"}
  ],
  "health_status": "OK"
}
```

**state_data JSONB Structure** (State_Data_Map snapshot):
```json
{
  "node_ip": "10.20.30.40",
  "node_user": "admin",
  "version": "7.0R1",
  "interface_count": 24,
  "dynamic_var_1": "extracted_value"
}
```

#### command_results
```sql
CREATE TABLE command_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    node_result_id UUID REFERENCES node_results(id) ON DELETE CASCADE NOT NULL,
    command_id INT NOT NULL,
    command_text TEXT NOT NULL,
    output TEXT,  -- Raw command output
    parsed_output JSONB,  -- Structured parser output
    status VARCHAR(50) NOT NULL
        CHECK (status IN ('success', 'failed', 'timeout', 'skipped')),
    parser_used VARCHAR(255),
    execution_time_ms INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(node_result_id, command_id)
);

CREATE INDEX idx_command_results_node_result_id ON command_results(node_result_id);
CREATE INDEX idx_command_results_status ON command_results(status);
CREATE INDEX idx_command_results_command_id ON command_results(command_id);
```

#### parsers
```sql
CREATE TABLE parsers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(50) NOT NULL,
    parser_type VARCHAR(50) NOT NULL 
        CHECK (parser_type IN ('regex', 'table', 'json', 'xml', 'custom')),
    code TEXT NOT NULL,  -- Python parser code
    config JSONB,  -- Parser-specific configuration
    description TEXT,
    created_by UUID REFERENCES users(id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(name, domain)
);

CREATE INDEX idx_parsers_name ON parsers(name);
CREATE INDEX idx_parsers_domain ON parsers(domain);
CREATE INDEX idx_parsers_type ON parsers(parser_type);
CREATE INDEX idx_parsers_active ON parsers(is_active) WHERE is_active = true;
```

**Parser config JSONB Example** (for RegexParser):
```json
{
  "patterns": {
    "version": "Version:\\s+([\\d\\.]+)",
    "uptime": "Uptime:\\s+([\\d\\s\\w]+)"
  },
  "field_destinations": {
    "version": "both",
    "uptime": "output"
  }
}
```

#### schedules
```sql
CREATE TABLE schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    activity_id UUID REFERENCES activities(id) NOT NULL,
    user_id UUID REFERENCES users(id) NOT NULL,
    cron_expression VARCHAR(100),  -- For recurring
    one_time_execution_at TIMESTAMP,  -- For one-time
    input_data JSONB NOT NULL,
    next_execution_at TIMESTAMP NOT NULL,
    is_recurring BOOLEAN DEFAULT false,
    active BOOLEAN DEFAULT true,
    last_execution_id UUID REFERENCES executions(id),
    last_executed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT one_schedule_type CHECK (
        (cron_expression IS NOT NULL AND one_time_execution_at IS NULL) OR
        (cron_expression IS NULL AND one_time_execution_at IS NOT NULL)
    )
);

CREATE INDEX idx_schedules_next_execution ON schedules(next_execution_at) WHERE active = true;
CREATE INDEX idx_schedules_activity_id ON schedules(activity_id);
CREATE INDEX idx_schedules_user_id ON schedules(user_id);
```

#### audit_logs
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(255),
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);

-- Partition by month for performance
CREATE TABLE audit_logs_2026_06 PARTITION OF audit_logs
    FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
```

#### templates
```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vendor VARCHAR(50) NOT NULL,
    device_type VARCHAR(100),
    command_text TEXT NOT NULL,
    description TEXT,
    use_case VARCHAR(255),
    tags TEXT[],  -- Array of tags
    contributed_by UUID REFERENCES users(id),
    is_approved BOOLEAN DEFAULT false,
    popularity_score INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_templates_vendor ON templates(vendor);
CREATE INDEX idx_templates_tags ON templates USING GIN(tags);
CREATE INDEX idx_templates_approved ON templates(is_approved) WHERE is_approved = true;
```

#### example_outputs
```sql
CREATE TABLE example_outputs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES templates(id) ON DELETE CASCADE NOT NULL,
    output_text TEXT NOT NULL,
    output_type VARCHAR(50) NOT NULL CHECK (output_type IN ('success', 'error', 'warning')),
    contributed_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_example_outputs_template_id ON example_outputs(template_id);
CREATE INDEX idx_example_outputs_type ON example_outputs(output_type);
```

---

## 2. API Endpoint Specifications

### 2.1 Authentication Endpoints

#### POST /api/v1/auth/login
**Purpose**: Authenticate user and return JWT token

**Request**:
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "engineer"
  }
}
```

**Error Response** (401 Unauthorized):
```json
{
  "error_type": "AuthenticationError",
  "message": "Invalid credentials",
  "details": {
    "remaining_attempts": 2
  }
}
```

**Business Logic**:
```python
def login(email: str, password: str) -> dict:
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise AuthenticationError("Invalid credentials")
    
    if user.account_locked_until and user.account_locked_until > datetime.now():
        raise AuthenticationError("Account temporarily locked")
    
    if not verify_password(password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 3:
            user.account_locked_until = datetime.now() + timedelta(minutes=15)
        db.commit()
        raise AuthenticationError("Invalid credentials")
    
    # Reset failed attempts on success
    user.failed_login_attempts = 0
    user.last_login_at = datetime.now()
    db.commit()
    
    access_token = create_jwt(user.id, expires_in=86400)
    refresh_token = create_jwt(user.id, expires_in=604800)
    
    # Audit log
    create_audit_log(user.id, "login", "user", user.id, success=True)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict()
    }
```

### 2.2 Execution Endpoints

#### POST /api/v1/executions
**Purpose**: Start a new automation execution

**Request**:
```json
{
  "activity_id": "uuid",
  "cr_id": "CR-2026-001",
  "execution_mode": "parallel",
  "max_parallelism": 50,
  "input_data": {
    "nodes": [
      {
        "node_name": "NOKIA_001",
        "node_ip": "10.1.1.1",
        "node_user": "admin",
        "node_password": "encrypted"
      }
    ]
  }
}
```

**Response** (202 Accepted):
```json
{
  "execution_id": "uuid",
  "status": "queued",
  "message": "Execution queued successfully",
  "estimated_start_time": "2026-06-09T15:30:00Z"
}
```

**Validation Rules**:
- `activity_id` must exist and be active
- `execution_mode` must be one of: sequential, parallel, batch
- `max_parallelism` must be between 1 and 200
- `input_data.nodes` must not be empty
- Each node must have: node_name, node_ip, node_user, node_password
- User must have `execute_automation` permission

**Business Logic**:
```python
@router.post("/executions", status_code=202)
@require_permission("execute_automation")
async def create_execution(
    request: ExecutionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ExecutionResponse:
    # 1. Validate activity exists
    activity = db.query(Activity).filter(
        Activity.id == request.activity_id,
        Activity.is_active == True
    ).first()
    if not activity:
        raise ValidationError("Activity not found or inactive")
    
    # 2. Validate input data against activity requirements
    validate_input_data(request.input_data, activity.config)
    
    # 3. Create execution record
    execution = Execution(
        user_id=current_user.id,
        activity_id=request.activity_id,
        cr_id=request.cr_id,
        status="queued",
        execution_mode=request.execution_mode,
        input_data=request.input_data,
        max_parallelism=request.max_parallelism,
        total_nodes=len(request.input_data["nodes"])
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    
    # 4. Publish to message queue
    message = {
        "execution_id": str(execution.id),
        "activity_id": str(activity.id),
        "user_id": str(current_user.id),
        "timestamp": datetime.now().isoformat()
    }
    publish_to_queue("automation_requests", message, priority=1)
    
    # 5. Audit log
    create_audit_log(
        current_user.id, "create_execution", "execution",
        str(execution.id), success=True
    )
    
    return ExecutionResponse.from_orm(execution)
```

#### GET /api/v1/executions/{execution_id}
**Purpose**: Get execution status and results

**Response** (200 OK):
```json
{
  "execution_id": "uuid",
  "activity_name": "Nokia_MPBN_Precheck",
  "status": "running",
  "progress": 45.5,
  "total_nodes": 100,
  "successful_nodes": 40,
  "failed_nodes": 5,
  "running_nodes": 10,
  "pending_nodes": 45,
  "created_at": "2026-06-09T15:25:00Z",
  "started_at": "2026-06-09T15:26:00Z",
  "estimated_completion": "2026-06-09T15:35:00Z",
  "node_results": [
    {
      "node_name": "NOKIA_001",
      "node_ip": "10.1.1.1",
      "status": "completed",
      "completed_at": "2026-06-09T15:28:00Z"
    }
  ]
}
```

### 2.3 Activity Endpoints

#### POST /api/v1/activities
**Purpose**: Create new activity from YAML configuration

**Request**:
```json
{
  "name": "Nokia_Health_Check",
  "domain": "ran",
  "description": "Health check for Nokia RAN nodes",
  "config": { /* activity config JSONB */ }
}
```

**Response** (201 Created):
```json
{
  "activity_id": "uuid",
  "name": "Nokia_Health_Check",
  "domain": "ran",
  "version": 1,
  "created_at": "2026-06-09T15:30:00Z"
}
```

**Validation Logic**:
```python
class ActivityConfigValidator:
    @staticmethod
    def validate(config: dict) -> None:
        required_keys = ["activity", "execution", "commands"]
        for key in required_keys:
            if key not in config:
                raise ValidationError(f"Missing required key: {key}")
        
        # Validate activity metadata
        activity = config["activity"]
        if "name" not in activity or "domain" not in activity:
            raise ValidationError("Activity must have name and domain")
        
        # Validate execution config
        execution = config["execution"]
        valid_modes = ["sequential", "parallel", "batch"]
        if execution.get("mode") not in valid_modes:
            raise ValidationError(f"Invalid execution mode: {execution.get('mode')}")
        
        # Validate commands
        commands = config["commands"]
        if not commands or not isinstance(commands, list):
            raise ValidationError("Commands must be a non-empty list")
        
        command_ids = set()
        for cmd in commands:
            if "command_id" not in cmd:
                raise ValidationError("Each command must have command_id")
            
            cmd_id = cmd["command_id"]
            if cmd_id in command_ids:
                raise ValidationError(f"Duplicate command_id: {cmd_id}")
            command_ids.add(cmd_id)
            
            # Validate parser references
            if "parsers" in cmd:
                for parser_name in cmd["parsers"]:
                    if not parser_exists(parser_name, config["activity"]["domain"]):
                        raise ValidationError(f"Parser not found: {parser_name}")
            
            # Validate control flow
            if "on_success" in cmd and cmd["on_success"] not in command_ids and cmd["on_success"] != 0:
                raise ValidationError(f"Invalid on_success target: {cmd['on_success']}")
```

### 2.4 Parser Generation Endpoints

#### POST /api/v1/parsers/generate
**Purpose**: Generate parser code from field selections

**Request**:
```json
{
  "parser_name": "nokia_version_parser",
  "parser_type": "table",
  "example_output": "Version: 7.0R1\nUptime: 45 days",
  "field_selections": [
    {
      "field_name": "version",
      "start_pos": 9,
      "end_pos": 15,
      "destination": "both",
      "data_type": "string"
    },
    {
      "field_name": "uptime",
      "start_pos": 25,
      "end_pos": 32,
      "destination": "output",
      "data_type": "string"
    }
  ]
}
```

**Response** (200 OK):
```json
{
  "parser_code": "class NokiaVersionParser(BaseParser):\n    def parse(self, output: str) -> ParseResult:\n        ...",
  "test_code": "def test_nokia_version_parser():\n    ...",
  "preview_results": {
    "extracted_data": {
      "version": "7.0R1",
      "uptime": "45 days"
    },
    "state_variables": {
      "version": "7.0R1"
    }
  }
}
```

**Generation Algorithm**:
```python
class ParserCodeGenerator:
    def generate_from_selections(
        self, 
        parser_name: str,
        parser_type: str,
        example_output: str,
        field_selections: List[FieldSelection]
    ) -> str:
        if parser_type == "regex":
            return self._generate_regex_parser(parser_name, field_selections)
        elif parser_type == "table":
            return self._generate_table_parser(parser_name, field_selections)
        else:
            raise ValueError(f"Unsupported parser type: {parser_type}")
    
    def _generate_regex_parser(self, name: str, selections: List[FieldSelection]) -> str:
        class_name = to_pascal_case(name)
        patterns = {}
        
        for sel in selections:
            # Generate regex pattern from selection
            pattern = self._infer_pattern(sel, example_output)
            patterns[sel.field_name] = pattern
        
        code = f'''
from backend.parser_framework.base_parser import BaseParser, ParseResult

class {class_name}(BaseParser):
    """Auto-generated parser for {name}"""
    
    def __init__(self):
        self.patterns = {patterns}
    
    def parse(self, output: str) -> ParseResult:
        extracted_data = {{}}
        state_variables = {{}}
        
        for field_name, pattern in self.patterns.items():
            match = re.search(pattern, output)
            if match:
                value = match.group(1)
                
                # Determine destination
                destination = "{sel.destination}"
                if destination in ["output", "both"]:
                    extracted_data[field_name] = value
                if destination in ["state", "both"]:
                    state_variables[field_name] = value
        
        return ParseResult(
            extracted_data=extracted_data,
            state_variables=state_variables
        )
'''
        return code
```

---

## 3. Core Component Designs

### 3.1 SSH Client Wrapper

**Class Diagram**:
```python
from dataclasses import dataclass
from typing import Optional, Callable
import paramiko
import re
import time

@dataclass
class SSHConfig:
    host: str
    port: int = 22
    username: str
    password: Optional[str] = None
    key_filename: Optional[str] = None
    timeout: int = 30
    jump_host: Optional['SSHConfig'] = None

@dataclass
class CommandResult:
    output: str
    status: str  # "success" | "failed" | "timeout"
    execution_time_ms: int
    error_message: Optional[str] = None

class SSHClient:
    """Wrapper around Paramiko for robust SSH command execution"""
    
    def __init__(self, config: SSHConfig):
        self.config = config
        self.client: Optional[paramiko.SSHClient] = None
        self.shell: Optional[paramiko.Channel] = None
        self.is_connected = False
    
    def connect(self, retry_count: int = 3) -> None:
        """Connect to device with retry logic"""
        for attempt in range(retry_count):
            try:
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                
                if self.config.jump_host:
                    # Connect via jump host
                    self._connect_via_jump_host()
                else:
                    # Direct connection
                    self.client.connect(
                        hostname=self.config.host,
                        port=self.config.port,
                        username=self.config.username,
                        password=self.config.password,
                        key_filename=self.config.key_filename,
                        timeout=self.config.timeout
                    )
                
                self.shell = self.client.invoke_shell()
                self.is_connected = True
                return
                
            except (paramiko.SSHException, socket.error) as e:
                if attempt < retry_count - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise SSHConnectionError(f"Failed to connect after {retry_count} attempts: {e}")
    
    def execute_command(
        self,
        command: str,
        expect_prompt: str = "#",
        timeout: int = 30,
        on_output: Optional[Callable[[str], None]] = None
    ) -> CommandResult:
        """Execute command and wait for prompt"""
        if not self.is_connected:
            raise SSHConnectionError("Not connected to device")
        
        start_time = time.time()
        output_buffer = ""
        
        try:
            # Send command
            self.shell.send(command + "\n")
            
            # Wait for prompt
            prompt_pattern = re.compile(expect_prompt)
            end_time = start_time + timeout
            
            while time.time() < end_time:
                if self.shell.recv_ready():
                    chunk = self.shell.recv(4096).decode('utf-8', errors='ignore')
                    output_buffer += chunk
                    
                    if on_output:
                        on_output(chunk)
                    
                    # Check for prompt
                    if prompt_pattern.search(output_buffer):
                        break
                
                time.sleep(0.1)
            else:
                # Timeout reached
                return CommandResult(
                    output=output_buffer,
                    status="timeout",
                    execution_time_ms=int((time.time() - start_time) * 1000),
                    error_message=f"Timeout waiting for prompt: {expect_prompt}"
                )
            
            return CommandResult(
                output=output_buffer,
                status="success",
                execution_time_ms=int((time.time() - start_time) * 1000)
            )
            
        except Exception as e:
            return CommandResult(
                output=output_buffer,
                status="failed",
                execution_time_ms=int((time.time() - start_time) * 1000),
                error_message=str(e)
            )
    
    def _connect_via_jump_host(self) -> None:
        """Connect to target device via jump host"""
        jump_client = paramiko.SSHClient()
        jump_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect to jump host
        jump_client.connect(
            hostname=self.config.jump_host.host,
            username=self.config.jump_host.username,
            password=self.config.jump_host.password,
            timeout=self.config.timeout
        )
        
        # Open channel through jump host
        jump_transport = jump_client.get_transport()
        dest_addr = (self.config.host, self.config.port)
        jump_addr = (self.config.jump_host.host, self.config.jump_host.port)
        jump_channel = jump_transport.open_channel("direct-tcpip", dest_addr, jump_addr)
        
        # Connect to target device
        self.client.connect(
            username=self.config.username,
            password=self.config.password,
            sock=jump_channel,
            timeout=self.config.timeout
        )
    
    def disconnect(self) -> None:
        """Close SSH connection"""
        if self.shell:
            self.shell.close()
        if self.client:
            self.client.close()
        self.is_connected = False
```

### 3.2 Command Executor

**Class Design**:
```python
from typing import Dict, Any, List
import re

class StateDataMap:
    """Manages state variables during execution"""
    
    def __init__(self, initial_state: Dict[str, Any]):
        self._state = initial_state.copy()
        self._history: List[Dict[str, Any]] = [initial_state.copy()]
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        self._state[key] = value
        self._history.append(self._state.copy())
    
    def update(self, updates: Dict[str, Any]) -> None:
        self._state.update(updates)
        self._history.append(self._state.copy())
    
    def resolve_variables(self, text: str) -> str:
        """Replace <<<variable>>> with actual values"""
        pattern = r'<<<([^>]+)>>>'
        
        def replacer(match):
            var_name = match.group(1)
            value = self._state.get(var_name)
            if value is None:
                raise VariableResolutionError(f"Variable not found: {var_name}")
            return str(value)
        
        return re.sub(pattern, replacer, text)
    
    def snapshot(self) -> Dict[str, Any]:
        """Get current state snapshot"""
        return self._state.copy()
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get full state history"""
        return self._history.copy()

class CommandExecutor:
    """Executes command sequence with state management"""
    
    def __init__(
        self,
        ssh_client: SSHClient,
        activity_config: Dict[str, Any],
        parser_registry: 'ParserRegistry'
    ):
        self.ssh_client = ssh_client
        self.activity_config = activity_config
        self.parser_registry = parser_registry
        self.commands = activity_config["commands"]
        self.state_map: Optional[StateDataMap] = None
    
    def execute_sequence(
        self,
        node_pars: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute full command sequence for a node"""
        # Initialize state
        self.state_map = StateDataMap(node_pars)
        
        extracted_data = {}
        command_results = []
        current_command_id = 1
        
        while current_command_id != 0:
            # Find command by ID
            command = self._find_command(current_command_id)
            if not command:
                raise CommandNotFoundError(f"Command ID {current_command_id} not found")
            
            # Execute command
            result = self._execute_single_command(command)
            command_results.append(result)
            
            # Update extracted data
            if result.get("extracted_data"):
                extracted_data.update(result["extracted_data"])
            
            # Determine next command (control flow)
            if result["status"] == "success":
                current_command_id = command.get("on_success", 0)
            else:
                current_command_id = command.get("on_failure", 0)
        
        return {
            "extracted_data": extracted_data,
            "state_data": self.state_map.snapshot(),
            "command_results": command_results,
            "status": "completed"
        }
    
    def _execute_single_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single command with parsing"""
        command_id = command["command_id"]
        
        # Resolve variables in command template
        command_text = self.state_map.resolve_variables(command["template"])
        
        # Execute via SSH
        result = self.ssh_client.execute_command(
            command=command_text,
            expect_prompt=command.get("expect_prompt", "#"),
            timeout=command.get("timeout", 30)
        )
        
        # Apply parsers
        extracted_data = {}
        state_variables = {}
        
        if result.status == "success" and "parsers" in command:
            for parser_name in command["parsers"]:
                parser = self.parser_registry.get_parser(
                    parser_name,
                    self.activity_config["activity"]["domain"]
                )
                
                try:
                    parse_result = parser.parse(result.output)
                    extracted_data.update(parse_result.extracted_data)
                    state_variables.update(parse_result.state_variables)
                except Exception as e:
                    # Log parser error but continue
                    print(f"Parser {parser_name} failed: {e}")
        
        # Update state with parsed variables
        if state_variables:
            self.state_map.update(state_variables)
        
        return {
            "command_id": command_id,
            "command_text": command_text,
            "output": result.output,
            "status": result.status,
            "execution_time_ms": result.execution_time_ms,
            "extracted_data": extracted_data,
            "error_message": result.error_message
        }
    
    def _find_command(self, command_id: int) -> Optional[Dict[str, Any]]:
        """Find command by ID"""
        for cmd in self.commands:
            if cmd["command_id"] == command_id:
                return cmd
        return None
```

I'll continue with the remaining sections in the next message. Let me complete the LLD document:

<function_calls>
<invoke name="fsAppend">
<parameter name="path">DOCS/13_LOW_LEVEL_DESIGN.md

### 3.3 Parser Framework

**Base Parser Design**:
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class ParseResult:
    extracted_data: Dict[str, Any]  # For Output_Sheet
    state_variables: Dict[str, Any]  # For State_Data_Map
    
    def __post_init__(self):
        if self.extracted_data is None:
            self.extracted_data = {}
        if self.state_variables is None:
            self.state_variables = {}

class BaseParser(ABC):
    """Abstract base class for all parsers"""
    
    @abstractmethod
    def parse(self, output: str) -> ParseResult:
        """Parse command output and extract data"""
        pass
    
    def validate_output(self, output: str) -> bool:
        """Pre-parse validation (optional override)"""
        return bool(output and output.strip())

class ParserRegistry:
    """Registry for managing parser instances"""
    
    def __init__(self):
        self._parsers: Dict[str, type] = {}
    
    def register(self, name: str, domain: str):
        """Decorator to register parser class"""
        def decorator(parser_class: type):
            key = f"{domain}:{name}"
            self._parsers[key] = parser_class
            return parser_class
        return decorator
    
    def get_parser(self, name: str, domain: str) -> BaseParser:
        """Get parser instance"""
        key = f"{domain}:{name}"
        parser_class = self._parsers.get(key)
        if not parser_class:
            raise ParserNotFoundError(f"Parser not found: {key}")
        return parser_class()
    
    def list_parsers(self, domain: Optional[str] = None) -> List[str]:
        """List all registered parsers"""
        if domain:
            return [k for k in self._parsers.keys() if k.startswith(f"{domain}:")]
        return list(self._parsers.keys())

# Global registry instance
parser_registry = ParserRegistry()

# Example parser implementations
@parser_registry.register("nokia_version_parser", "ran")
class NokiaVersionParser(BaseParser):
    """Parser for Nokia version command output"""
    
    def __init__(self):
        self.patterns = {
            "version": r"Version:\s+([\d\.R]+)",
            "uptime": r"Uptime:\s+([\d\s\w]+)"
        }
    
    def parse(self, output: str) -> ParseResult:
        import re
        extracted_data = {}
        state_variables = {}
        
        for field_name, pattern in self.patterns.items():
            match = re.search(pattern, output)
            if match:
                value = match.group(1).strip()
                extracted_data[field_name] = value
                state_variables[field_name] = value  # Both for this example
        
        return ParseResult(
            extracted_data=extracted_data,
            state_variables=state_variables
        )

@parser_registry.register("table_parser", "common")
class TableParser(BaseParser):
    """Generic table parser for fixed-width or delimited tables"""
    
    def __init__(self, delimiter: str = None, headers: List[str] = None):
        self.delimiter = delimiter
        self.headers = headers
    
    def parse(self, output: str) -> ParseResult:
        lines = output.strip().split('\n')
        if not lines:
            return ParseResult({}, {})
        
        # Auto-detect headers if not provided
        if not self.headers:
            self.headers = self._extract_headers(lines[0])
        
        # Parse rows
        rows = []
        for line in lines[1:]:  # Skip header row
            if self.delimiter:
                values = line.split(self.delimiter)
            else:
                values = self._parse_fixed_width(line)
            
            if len(values) == len(self.headers):
                row = dict(zip(self.headers, [v.strip() for v in values]))
                rows.append(row)
        
        return ParseResult(
            extracted_data={"table_data": rows},
            state_variables={}
        )
    
    def _extract_headers(self, header_line: str) -> List[str]:
        """Extract column headers"""
        if self.delimiter:
            return [h.strip() for h in header_line.split(self.delimiter)]
        else:
            # Use whitespace as delimiter
            return header_line.split()
    
    def _parse_fixed_width(self, line: str) -> List[str]:
        """Parse fixed-width columns"""
        # Simple implementation: split on multiple spaces
        return [col.strip() for col in re.split(r'\s{2,}', line)]
```

---

## 4. Algorithm Designs

### 4.1 Variable Dependency Resolution

**Problem**: Resolve <<<variable>>> references in command templates where variables may be defined in previous commands

**Algorithm**:
```python
def resolve_variable_dependencies(commands: List[Dict], node_pars: Dict) -> None:
    """Validate all variables can be resolved"""
    available_vars = set(node_pars.keys())
    
    for cmd in commands:
        # Extract variables referenced in this command
        template = cmd.get("template", "")
        required_vars = set(re.findall(r'<<<([^>]+)>>>', template))
        
        # Check if all required vars are available
        missing_vars = required_vars - available_vars
        if missing_vars:
            raise VariableDependencyError(
                f"Command {cmd['command_id']} references undefined variables: {missing_vars}"
            )
        
        # Add variables that this command will define (from parser outputs)
        if "parsers" in cmd:
            for parser_name in cmd["parsers"]:
                parser_outputs = get_parser_outputs(parser_name)
                available_vars.update(parser_outputs)
```

### 4.2 Cron Expression Calculation

**Problem**: Calculate next execution time from cron expression

**Algorithm**:
```python
from croniter import croniter
from datetime import datetime

def calculate_next_execution(cron_expression: str, base_time: datetime = None) -> datetime:
    """Calculate next execution time from cron expression"""
    if base_time is None:
        base_time = datetime.now()
    
    try:
        cron = croniter(cron_expression, base_time)
        return cron.get_next(datetime)
    except Exception as e:
        raise CronParsingError(f"Invalid cron expression: {cron_expression}") from e

# Example cron expressions:
# "*/5 * * * *"     - Every 5 minutes
# "0 2 * * *"       - Daily at 2 AM
# "0 0 * * 0"       - Every Sunday at midnight
# "0 9-17 * * 1-5"  - Weekdays 9 AM to 5 PM
```

### 4.3 Parallel Execution with Concurrency Limit

**Problem**: Execute N node tasks in parallel with max concurrent limit

**Algorithm** (using Celery):
```python
from celery import group, chord
from typing import List

def execute_parallel_with_limit(
    execution_id: str,
    node_tasks: List[Dict],
    max_parallelism: int
) -> None:
    """Execute node tasks in parallel with concurrency limit"""
    
    # Chunk nodes based on max_parallelism
    chunks = [
        node_tasks[i:i + max_parallelism]
        for i in range(0, len(node_tasks), max_parallelism)
    ]
    
    # Execute chunks sequentially, nodes within chunk in parallel
    for chunk in chunks:
        # Create group of tasks for this chunk
        task_group = group([
            execute_node_task.si(execution_id, node)
            for node in chunk
        ])
        
        # Execute group and wait for completion
        result = task_group.apply_async()
        result.get()  # Wait for all tasks in chunk to complete
```

### 4.4 Parser Structure Detection

**Problem**: Auto-detect output structure (table, JSON, key-value, etc.)

**Algorithm**:
```python
import json
import xml.etree.ElementTree as ET

def detect_structure(output: str) -> Dict[str, Any]:
    """Detect structure of command output"""
    output = output.strip()
    
    # Try JSON
    try:
        json.loads(output)
        return {"type": "json", "confidence": 1.0}
    except:
        pass
    
    # Try XML
    try:
        ET.fromstring(output)
        return {"type": "xml", "confidence": 1.0}
    except:
        pass
    
    lines = output.split('\n')
    
    # Detect table (consistent column alignment)
    if is_table_format(lines):
        delimiter = detect_delimiter(lines[0])
        return {
            "type": "table",
            "delimiter": delimiter,
            "confidence": 0.9
        }
    
    # Detect key-value pairs
    kv_count = sum(1 for line in lines if ':' in line or '=' in line)
    if kv_count / len(lines) > 0.6:
        return {"type": "key_value", "confidence": 0.8}
    
    # Default to unstructured text
    return {"type": "text", "confidence": 0.5}

def is_table_format(lines: List[str]) -> bool:
    """Check if output looks like a table"""
    if len(lines) < 2:
        return False
    
    # Check for consistent column positions
    first_line_spaces = find_space_positions(lines[0])
    
    consistent_count = 0
    for line in lines[1:4]:  # Check first few lines
        line_spaces = find_space_positions(line)
        if similar_positions(first_line_spaces, line_spaces):
            consistent_count += 1
    
    return consistent_count >= 2

def find_space_positions(line: str) -> List[int]:
    """Find positions of multi-space gaps (column separators)"""
    return [m.start() for m in re.finditer(r'\s{2,}', line)]
```

---

## 5. Message Queue Design

### 5.1 Queue Structure

**RabbitMQ Queue Definitions**:
```python
from kombu import Exchange, Queue

# Define exchanges
default_exchange = Exchange('automation', type='direct')

# Define queues
QUEUES = [
    Queue(
        'automation_requests',
        exchange=default_exchange,
        routing_key='automation.request',
        queue_arguments={
            'x-message-ttl': 86400000,  # 24 hours
            'x-dead-letter-exchange': 'dlx',
            'x-dead-letter-routing-key': 'automation.request.dlq'
        }
    ),
    Queue(
        'node_executions',
        exchange=default_exchange,
        routing_key='automation.node',
        queue_arguments={
            'x-message-ttl': 3600000,  # 1 hour
            'x-max-priority': 10
        }
    ),
    Queue(
        'priority_executions',
        exchange=default_exchange,
        routing_key='automation.priority',
        queue_arguments={
            'x-max-priority': 10
        }
    )
]
```

### 5.2 Message Schema

**Execution Request Message**:
```json
{
  "message_id": "uuid",
  "execution_id": "uuid",
  "activity_id": "uuid",
  "user_id": "uuid",
  "priority": 5,
  "timestamp": "2026-06-09T15:30:00Z",
  "retry_count": 0,
  "idempotency_key": "exec_uuid_v1"
}
```

**Node Execution Message**:
```json
{
  "message_id": "uuid",
  "execution_id": "uuid",
  "node_name": "NOKIA_001",
  "node_pars": {
    "node_ip": "10.1.1.1",
    "node_user": "admin",
    "node_password": "encrypted"
  },
  "activity_config": { /* full config */ },
  "priority": 5,
  "timestamp": "2026-06-09T15:30:00Z"
}
```

### 5.3 Publisher with Retry

```python
from kombu import Connection, Producer
from kombu.exceptions import OperationalError
import time

class MessagePublisher:
    """Publishes messages with retry logic"""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
    
    def publish(
        self,
        queue_name: str,
        message: Dict[str, Any],
        priority: int = 5,
        retry_count: int = 5
    ) -> None:
        """Publish message with exponential backoff retry"""
        for attempt in range(retry_count):
            try:
                with Connection(self.connection_url) as conn:
                    with conn.Producer() as producer:
                        producer.publish(
                            message,
                            routing_key=f"automation.{queue_name.split('_')[0]}",
                            priority=priority,
                            retry=True,
                            retry_policy={
                                'max_retries': 3,
                                'interval_start': 0,
                                'interval_step': 2,
                                'interval_max': 30,
                            }
                        )
                return  # Success
                
            except OperationalError as e:
                if attempt < retry_count - 1:
                    sleep_time = 2 ** attempt  # Exponential backoff
                    time.sleep(sleep_time)
                    continue
                raise MessagePublishError(f"Failed to publish after {retry_count} attempts") from e
```

---

## 6. Configuration Schema

### 6.1 Activity YAML Schema

```yaml
# Activity configuration in YAML format
activity:
  name: Nokia_MPBN_Precheck
  domain: pbn
  description: Pre-migration health check for Nokia MPBN nodes
  version: 1.0

execution:
  mode: parallel  # sequential | parallel | batch
  max_parallelism: 50
  timeout_seconds: 600
  failure_policy: continue  # continue | stop_node | stop_all
  
  jump_host:
    use_jump_host: true
    oss_ip: <<<oss_ip>>>
    oss_user: <<<oss_user>>>
    oss_password: <<<oss_password>>>

commands:
  - command_id: 1
    template: "show version"
    expect_prompt: "#"
    timeout: 30
    parsers:
      - nokia_version_parser
    on_success: 2
    on_failure: 0
  
  - command_id: 2
    template: "show interface <<<interface_name>>>"
    expect_prompt: "#"
    timeout: 30
    parsers:
      - nokia_interface_parser
    on_success: 3
    on_failure: 0

additional_module:
  enabled: true
  modules:
    - type: email_notification
      config:
        recipients: ["team@example.com"]
        subject: "Execution Complete: Nokia_MPBN_Precheck"
    
    - type: csv_merger
      config:
        output_file: "merged_results.xlsx"
```

### 6.2 JSON Schema for Validation

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Activity Configuration Schema",
  "type": "object",
  "required": ["activity", "execution", "commands"],
  "properties": {
    "activity": {
      "type": "object",
      "required": ["name", "domain"],
      "properties": {
        "name": {"type": "string", "minLength": 1},
        "domain": {
          "type": "string",
          "enum": ["ran", "core", "pbn", "paco", "txn", "core2"]
        },
        "description": {"type": "string"}
      }
    },
    "execution": {
      "type": "object",
      "required": ["mode"],
      "properties": {
        "mode": {
          "type": "string",
          "enum": ["sequential", "parallel", "batch"]
        },
        "max_parallelism": {
          "type": "integer",
          "minimum": 1,
          "maximum": 200
        },
        "timeout_seconds": {
          "type": "integer",
          "minimum": 1
        },
        "failure_policy": {
          "type": "string",
          "enum": ["continue", "stop_node", "stop_all"]
        }
      }
    },
    "commands": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["command_id", "template"],
        "properties": {
          "command_id": {"type": "integer", "minimum": 1},
          "template": {"type": "string", "minLength": 1},
          "expect_prompt": {"type": "string", "default": "#"},
          "timeout": {"type": "integer", "minimum": 1, "default": 30},
          "parsers": {
            "type": "array",
            "items": {"type": "string"}
          },
          "on_success": {"type": "integer", "minimum": 0},
          "on_failure": {"type": "integer", "minimum": 0}
        }
      }
    }
  }
}
```

---

## Document Revision History

| Version | Date       | Author | Changes                          |
|---------|------------|--------|----------------------------------|
| 1.0     | 2026-06-09 | System | Initial LLD document creation    |

---

## Appendices

### A. Code Examples

Complete working examples are provided in the `examples/` directory:
- `examples/ssh_client_usage.py` - SSH client usage
- `examples/parser_creation.py` - Creating custom parsers
- `examples/activity_execution.py` - Executing activities programmatically

### B. Testing Examples

Property-based test examples:
- `tests/property/test_variable_resolution.py`
- `tests/property/test_state_accumulation.py`
- `tests/property/test_parser_extraction.py`

### C. References

- High-Level Design: `DOCS/12_HIGH_LEVEL_DESIGN.md`
- Design Document: `.kiro/specs/telecom-automation-platform/design.md`
- Requirements: `.kiro/specs/telecom-automation-platform/requirements.md`
- API Documentation: Generated at `/docs` endpoint
