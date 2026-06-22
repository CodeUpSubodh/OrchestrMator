# Phase 2: Core API Gateway - Detailed Specification

## Overview

This document provides comprehensive API contracts, business logic, and implementation guidelines for Phase 2 (Core API Gateway). Use this as a reference when working with AI coding assistants.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  Middleware Layer                                            │
│  - CORS Middleware                                           │
│  - Exception Handler                                         │
│  - Logging Middleware                                        │
│  - JWT Authentication                                        │
├─────────────────────────────────────────────────────────────┤
│  API Routes                                                  │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐ │
│  │ Auth Routes  │ Activity     │ Execution    │ Health   │ │
│  │              │ Routes       │ Routes       │ Check    │ │
│  └──────────────┴──────────────┴──────────────┴──────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Database Layer (SQLAlchemy)                                 │
│  - User Model                                                │
│  - Activity Model                                            │
│  - Execution Model                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Task 2.1: Create FastAPI Application

### File: `backend/api_gateway/main.py`


#### Purpose
Initialize the FastAPI application with all necessary middleware, error handlers, and configuration.

#### Implementation Requirements

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

app = FastAPI(
    title="OrchestrMator API",
    description="Telecom Automation Platform API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )
```


---

## Task 2.2: Implement Authentication

### File: `backend/api_gateway/auth.py`

#### JWT Utility Functions

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# Configuration
SECRET_KEY = "your-secret-key-here"  # Load from environment
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token
    
    Args:
        data: Payload to encode (should include user_id, email, role)
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token with longer expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
```


### File: `backend/api_gateway/routes/auth.py`

---

### **Endpoint 1: Register User**

**Route:** `POST /api/v1/auth/register`

**Purpose:** Create a new user account

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "role": "user"  // Optional, defaults to "user"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2026-06-22T10:30:00Z"
}
```

**Business Logic:**
1. Validate email format (use `email-validator` library)
2. Check if email already exists in database
3. Validate password strength (min 8 chars, uppercase, lowercase, digit)
4. Hash password using bcrypt (call `user.set_password(password)`)
5. Create user record in database with `is_active=True`
6. Return user data (exclude password_hash)

**Error Responses:**
- `400 Bad Request`: Invalid email format or weak password
- `409 Conflict`: Email already registered

**Implementation Hints:**
```python
from backend.models.user import User
from backend.schemas.user import UserCreate, UserResponse

@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if email exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
    
    # Create user
    user = User(email=user_data.email, role=user_data.role or "user")
    user.set_password(user_data.password)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user
```


---

### **Endpoint 2: Login**

**Route:** `POST /api/v1/auth/login`

**Purpose:** Authenticate user and return JWT tokens

**Request Body (OAuth2 Form):**
```
username=user@example.com  // Note: Called "username" but should be email
password=SecurePass123!
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,  // 30 minutes in seconds
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "user"
  }
}
```

**Business Logic:**
1. Query user by email
2. Check if user exists and is active
3. Verify password using `user.verify_password(password)`
4. Create access token with user data (id, email, role)
5. Create refresh token with user id only
6. Return both tokens and user info

**Error Responses:**
- `401 Unauthorized`: Invalid credentials or inactive account

**Implementation Hints:**
```python
from fastapi.security import OAuth2PasswordRequestForm

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Find user by email (form_data.username contains email)
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not user.verify_password(form_data.password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")
    
    # Create tokens
    access_token = create_access_token(
        data={"user_id": user.id, "email": user.email, "role": user.role}
    )
    refresh_token = create_refresh_token(data={"user_id": user.id})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {"id": user.id, "email": user.email, "role": user.role}
    }
```


---

### **Endpoint 3: Refresh Token**

**Route:** `POST /api/v1/auth/refresh`

**Purpose:** Get new access token using refresh token

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Business Logic:**
1. Decode refresh token
2. Verify token type is "refresh"
3. Extract user_id from token
4. Query user from database
5. Verify user is still active
6. Create new access token
7. Return new access token

**Error Responses:**
- `401 Unauthorized`: Invalid or expired refresh token
- `403 Forbidden`: User account is no longer active

---

### **Endpoint 4: Get Current User**

**Route:** `GET /api/v1/auth/me`

**Purpose:** Get authenticated user's information

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2026-06-22T10:30:00Z",
  "updated_at": "2026-06-22T10:30:00Z"
}
```

**Business Logic:**
1. Extract token from Authorization header
2. Decode and validate JWT token
3. Extract user_id from token payload
4. Query user from database
5. Return user data

**Error Responses:**
- `401 Unauthorized`: Missing, invalid, or expired token

**Implementation Hints:**
```python
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Dependency to get current authenticated user"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```


---

## Task 2.3: Implement Activity CRUD

### File: `backend/api_gateway/routes/activities.py`

---

### **Endpoint 1: List Activities**

**Route:** `GET /api/v1/activities`

**Purpose:** Get paginated list of activities with optional filtering

**Query Parameters:**
- `page` (int, default=1): Page number
- `page_size` (int, default=20): Items per page
- `domain` (string, optional): Filter by domain (e.g., "NOKIA", "CISCO")
- `is_active` (boolean, optional): Filter by active status
- `search` (string, optional): Search in name and description
- `created_by` (int, optional): Filter by creator user ID

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "name": "MPBN_PRECHECK",
      "domain": "NOKIA",
      "description": "Pre-check automation for MPBN maintenance",
      "version": "1.0.0",
      "is_active": true,
      "created_by": 1,
      "created_at": "2026-06-22T10:30:00Z",
      "updated_at": "2026-06-22T10:30:00Z"
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

**Business Logic:**
1. Build query with filters (domain, is_active, search, created_by)
2. For search: use ILIKE on name and description
3. Calculate pagination (skip = (page-1) * page_size)
4. Execute query with limit and offset
5. Count total matching records
6. Return paginated results with metadata

**Implementation Hints:**
```python
@router.get("/activities", response_model=ActivityListResponse)
async def list_activities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    created_by: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Build base query
    query = db.query(Activity)
    
    # Apply filters
    if domain:
        query = query.filter(Activity.domain == domain)
    if is_active is not None:
        query = query.filter(Activity.is_active == is_active)
    if search:
        query = query.filter(
            or_(
                Activity.name.ilike(f"%{search}%"),
                Activity.description.ilike(f"%{search}%")
            )
        )
    if created_by:
        query = query.filter(Activity.created_by == created_by)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    skip = (page - 1) * page_size
    items = query.offset(skip).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }
```


---

### **Endpoint 2: Create Activity**

**Route:** `POST /api/v1/activities`

**Purpose:** Create a new automation activity configuration

**Request Body:**
```json
{
  "name": "MPBN_PRECHECK",
  "domain": "NOKIA",
  "description": "Pre-check automation for MPBN maintenance",
  "version": "1.0.0",
  "git_commit_sha": "abc123def456",
  "config": {
    "commands": [
      {
        "command_id": "CMD_001",
        "command": "show version",
        "expect_prompt": "#",
        "timeout": 30,
        "parser": "nokia_version_parser"
      }
    ],
    "authentication": {
      "type": "direct_ssh",
      "username": "admin"
    },
    "state_data_map": {
      "node_ip": "",
      "cr_id": "",
      "custom_var": "default_value"
    }
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "MPBN_PRECHECK",
  "domain": "NOKIA",
  "description": "Pre-check automation for MPBN maintenance",
  "version": "1.0.0",
  "git_commit_sha": "abc123def456",
  "config": { ... },
  "is_active": true,
  "created_by": 1,
  "created_at": "2026-06-22T10:30:00Z",
  "updated_at": "2026-06-22T10:30:00Z"
}
```

**Business Logic:**
1. Validate required fields (name, domain, config)
2. Validate config structure:
   - Must have "commands" array
   - Must have "authentication" object
   - Must have "state_data_map" object
3. Check if activity name already exists (unique per domain)
4. Set created_by to current user's ID
5. Set is_active to true by default
6. Create activity record in database
7. Return created activity

**Error Responses:**
- `400 Bad Request`: Invalid config structure
- `409 Conflict`: Activity name already exists in this domain

**Config Validation Rules:**
```python
# Command structure validation
- command_id: required, string
- command: required, string
- expect_prompt: optional, string
- timeout: optional, integer (default 30)
- parser: optional, string
- on_success: optional, string (GOTO or CONTINUE)
- on_failure: optional, string (STOP or GOTO)

# Authentication types
- direct_ssh: username/password
- jump_host: OSS + target node
- key_based: SSH key authentication

# State Data Map
- Can contain any key-value pairs
- Values can be empty strings (filled at runtime)
```


---

### **Endpoint 3: Get Activity Details**

**Route:** `GET /api/v1/activities/{id}`

**Purpose:** Get full details of a specific activity

**Path Parameters:**
- `id` (int): Activity ID

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "MPBN_PRECHECK",
  "domain": "NOKIA",
  "description": "Pre-check automation for MPBN maintenance",
  "version": "1.0.0",
  "git_commit_sha": "abc123def456",
  "config": { ... },
  "is_active": true,
  "created_by": 1,
  "created_at": "2026-06-22T10:30:00Z",
  "updated_at": "2026-06-22T10:30:00Z"
}
```

**Business Logic:**
1. Query activity by ID
2. Return activity if found

**Error Responses:**
- `404 Not Found`: Activity doesn't exist

---

### **Endpoint 4: Update Activity**

**Route:** `PUT /api/v1/activities/{id}`

**Purpose:** Update an existing activity configuration

**Path Parameters:**
- `id` (int): Activity ID

**Request Body:**
```json
{
  "name": "MPBN_PRECHECK",
  "description": "Updated description",
  "version": "1.1.0",
  "config": { ... },
  "is_active": true
}
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "MPBN_PRECHECK",
  "domain": "NOKIA",
  "description": "Updated description",
  "version": "1.1.0",
  ...
}
```

**Business Logic:**
1. Query activity by ID
2. Check if activity exists
3. Check if current user is the creator OR has admin role
4. Validate updated config structure (if config is being updated)
5. Update only provided fields
6. Update updated_at timestamp automatically (handled by TimestampMixin)
7. Save changes to database
8. Return updated activity

**Error Responses:**
- `404 Not Found`: Activity doesn't exist
- `403 Forbidden`: User doesn't have permission to update
- `400 Bad Request`: Invalid config structure

**Implementation Hints:**
```python
@router.put("/activities/{id}", response_model=ActivityResponse)
async def update_activity(
    id: int,
    activity_update: ActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get activity
    activity = db.query(Activity).filter(Activity.id == id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # Check permissions
    if activity.created_by != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Update fields
    for field, value in activity_update.dict(exclude_unset=True).items():
        setattr(activity, field, value)
    
    db.commit()
    db.refresh(activity)
    
    return activity
```


---

### **Endpoint 5: Delete/Deactivate Activity**

**Route:** `DELETE /api/v1/activities/{id}`

**Purpose:** Soft-delete activity by setting is_active=False

**Path Parameters:**
- `id` (int): Activity ID

**Response (200 OK):**
```json
{
  "message": "Activity deactivated successfully",
  "id": 1
}
```

**Business Logic:**
1. Query activity by ID
2. Check if activity exists
3. Check if current user is the creator OR has admin role
4. Set is_active = False (soft delete - don't actually delete record)
5. Save changes to database
6. Return success message

**Error Responses:**
- `404 Not Found`: Activity doesn't exist
- `403 Forbidden`: User doesn't have permission to delete

**Note:** We use soft delete (is_active=False) instead of hard delete to maintain historical data integrity and allow for executions that reference this activity.

---

## Task 2.4: Implement Execution Endpoints

### File: `backend/api_gateway/routes/executions.py`

---

### **Endpoint 1: Start Execution**

**Route:** `POST /api/v1/executions`

**Purpose:** Create and start a new automation execution

**Request Body:**
```json
{
  "activity_id": 1,
  "cr_id": "CR123456",
  "execution_mode": "parallel",
  "max_parallelism": 10,
  "input_data": {
    "nodes": [
      {
        "node_name": "ROUTER01",
        "node_ip": "10.20.30.40",
        "credentials": {
          "username": "admin",
          "password": "encrypted_password"
        },
        "custom_params": {
          "region": "EAST",
          "site_id": "SITE001"
        }
      }
    ],
    "global_params": {
      "maintenance_window": "2026-06-22 22:00-24:00",
      "approval_id": "APPR789"
    }
  }
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "activity_id": 1,
  "cr_id": "CR123456",
  "status": "queued",
  "execution_mode": "parallel",
  "max_parallelism": 10,
  "input_data": { ... },
  "trigger_source": "api",
  "trigger_metadata": {
    "user_id": 1,
    "user_email": "user@example.com",
    "ip_address": "192.168.1.100"
  },
  "created_at": "2026-06-22T10:30:00Z",
  "created_by": 1
}
```

**Business Logic:**
1. Validate activity_id exists and is_active=true
2. Validate execution_mode is one of: "sequential", "parallel", "batch"
3. Validate input_data structure:
   - Must have "nodes" array with at least 1 node
   - Each node must have: node_name, node_ip
   - Validate IP address format
4. Set status = "queued" (initial status)
5. Set user_id = current_user.id
6. Set trigger_source = "api"
7. Set trigger_metadata with user info and request IP
8. Create execution record in database
9. **TODO in Phase 3:** Publish message to RabbitMQ queue
10. Return execution details

**Error Responses:**
- `400 Bad Request`: Invalid input_data structure or execution_mode
- `404 Not Found`: Activity doesn't exist
- `422 Unprocessable Entity`: Activity is inactive

**Input Data Validation:**
```python
# Required fields in input_data
- nodes: list (min length 1)
  - node_name: string (required)
  - node_ip: string (required, valid IP)
  - credentials: dict (optional, but usually needed)
  - custom_params: dict (optional)
- global_params: dict (optional)

# Execution modes
- sequential: Execute nodes one at a time
- parallel: Execute all nodes simultaneously (respect max_parallelism)
- batch: Group nodes into batches
```


---

### **Endpoint 2: List Executions**

**Route:** `GET /api/v1/executions`

**Purpose:** Get paginated list of executions with filtering

**Query Parameters:**
- `page` (int, default=1): Page number
- `page_size` (int, default=20): Items per page
- `activity_id` (int, optional): Filter by activity
- `status` (string, optional): Filter by status (queued, running, completed, failed, cancelled)
- `cr_id` (string, optional): Filter by CR ID
- `user_id` (int, optional): Filter by user who created execution
- `from_date` (datetime, optional): Filter executions after this date
- `to_date` (datetime, optional): Filter executions before this date

**Response (200 OK):**
```json
{
  "items": [
    {
      "id": 1,
      "activity_id": 1,
      "activity_name": "MPBN_PRECHECK",
      "cr_id": "CR123456",
      "status": "completed",
      "execution_mode": "parallel",
      "created_at": "2026-06-22T10:30:00Z",
      "completed_at": "2026-06-22T10:45:00Z",
      "total_nodes": 50,
      "successful_nodes": 48,
      "failed_nodes": 2
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

**Business Logic:**
1. Build query with filters
2. Join with Activity table to get activity_name
3. Left join with NodeResult to get statistics (total_nodes, successful_nodes, failed_nodes)
4. Apply date range filters if provided
5. Order by created_at DESC (most recent first)
6. Apply pagination
7. Return paginated results

**Status Values:**
- `queued`: Execution created but not started
- `running`: Currently executing
- `completed`: All nodes finished successfully
- `partial_success`: Some nodes failed but execution completed
- `failed`: Execution failed completely
- `cancelled`: User cancelled execution

---

### **Endpoint 3: Get Execution Details**

**Route:** `GET /api/v1/executions/{id}`

**Purpose:** Get detailed information about a specific execution

**Path Parameters:**
- `id` (int): Execution ID

**Response (200 OK):**
```json
{
  "id": 1,
  "activity_id": 1,
  "activity": {
    "id": 1,
    "name": "MPBN_PRECHECK",
    "domain": "NOKIA"
  },
  "cr_id": "CR123456",
  "status": "completed",
  "execution_mode": "parallel",
  "max_parallelism": 10,
  "input_data": { ... },
  "trigger_source": "api",
  "trigger_metadata": { ... },
  "created_at": "2026-06-22T10:30:00Z",
  "started_at": "2026-06-22T10:31:00Z",
  "completed_at": "2026-06-22T10:45:00Z",
  "created_by": 1,
  "statistics": {
    "total_nodes": 50,
    "successful_nodes": 48,
    "failed_nodes": 2,
    "skipped_nodes": 0,
    "total_commands": 250,
    "successful_commands": 240,
    "failed_commands": 10,
    "execution_time_seconds": 840
  }
}
```

**Business Logic:**
1. Query execution by ID with eager loading of activity
2. Calculate statistics from related NodeResult records:
   - Count nodes by status
   - Count commands from CommandResult records
   - Calculate execution time (completed_at - started_at)
3. Return execution details with statistics

**Error Responses:**
- `404 Not Found`: Execution doesn't exist


---

### **Endpoint 4: Get Execution Results**

**Route:** `GET /api/v1/executions/{id}/results`

**Purpose:** Get detailed results for all nodes in an execution

**Path Parameters:**
- `id` (int): Execution ID

**Query Parameters:**
- `node_name` (string, optional): Filter by node name
- `status` (string, optional): Filter by node status
- `include_commands` (boolean, default=true): Include command results

**Response (200 OK):**
```json
{
  "execution_id": 1,
  "results": [
    {
      "node_result_id": 1,
      "node_name": "ROUTER01",
      "node_ip": "10.20.30.40",
      "status": "success",
      "extracted_data": {
        "software_version": "7.0R1",
        "chassis_type": "7750 SR",
        "total_ports": 48
      },
      "state_data": {
        "node_ip": "10.20.30.40",
        "cr_id": "CR123456",
        "custom_var": "value"
      },
      "log_file_path": "s3://bucket/executions/1/ROUTER01.log",
      "started_at": "2026-06-22T10:31:00Z",
      "completed_at": "2026-06-22T10:33:00Z",
      "commands": [
        {
          "command_id": "CMD_001",
          "command_text": "show version",
          "output": "Nokia 7750 SR...",
          "parsed_output": {
            "version": "7.0R1",
            "build": "12345"
          },
          "parser_used": "nokia_version_parser",
          "status": "success",
          "execution_time_ms": 1250
        }
      ],
      "error_message": null
    }
  ]
}
```

**Business Logic:**
1. Query execution to verify it exists
2. Query all NodeResult records for this execution
3. Apply filters (node_name, status)
4. If include_commands=true, eager load CommandResult records
5. Order by node_name
6. Return results

**Error Responses:**
- `404 Not Found`: Execution doesn't exist

---

### **Endpoint 5: Cancel Execution**

**Route:** `DELETE /api/v1/executions/{id}`

**Purpose:** Cancel a running or queued execution

**Path Parameters:**
- `id` (int): Execution ID

**Response (200 OK):**
```json
{
  "message": "Execution cancelled successfully",
  "id": 1,
  "status": "cancelled"
}
```

**Business Logic:**
1. Query execution by ID
2. Check if execution exists
3. Check if current user created this execution OR has admin role
4. Verify execution is in cancellable state (queued or running)
5. Set status = "cancelled"
6. **TODO in Phase 3:** Send cancellation signal to worker
7. Save changes to database
8. Return success message

**Error Responses:**
- `404 Not Found`: Execution doesn't exist
- `403 Forbidden`: User doesn't have permission to cancel
- `400 Bad Request`: Execution already completed or cancelled

**Cancellable States:**
- `queued`: Can be cancelled (remove from queue)
- `running`: Can be cancelled (stop workers gracefully)

**Non-Cancellable States:**
- `completed`: Already finished
- `failed`: Already finished
- `cancelled`: Already cancelled


---

## Task 2.5: Add Health Check

### File: `backend/api_gateway/routes/health.py`

---

### **Endpoint 1: Basic Health Check**

**Route:** `GET /health`

**Purpose:** Simple health check for load balancers

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2026-06-22T10:30:00Z",
  "version": "1.0.0"
}
```

**Business Logic:**
- Always return 200 OK if application is running
- Used by load balancers for basic connectivity check

---

### **Endpoint 2: Readiness Check**

**Route:** `GET /health/ready`

**Purpose:** Check if application is ready to serve requests (all dependencies available)

**Response (200 OK):**
```json
{
  "status": "ready",
  "checks": {
    "database": "healthy",
    "redis": "healthy",
    "rabbitmq": "healthy"
  },
  "timestamp": "2026-06-22T10:30:00Z"
}
```

**Response (503 Service Unavailable):**
```json
{
  "status": "not_ready",
  "checks": {
    "database": "healthy",
    "redis": "unhealthy",
    "rabbitmq": "healthy"
  },
  "timestamp": "2026-06-22T10:30:00Z"
}
```

**Business Logic:**
1. Test database connection (execute simple query: SELECT 1)
2. Test Redis connection (execute PING)
3. Test RabbitMQ connection (check if connected)
4. If all checks pass: return 200 with status="ready"
5. If any check fails: return 503 with status="not_ready"

**Implementation Hints:**
```python
@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    checks = {}
    all_healthy = True
    
    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = "unhealthy"
        all_healthy = False
    
    # Redis check (Phase 3)
    # Try ping Redis
    
    # RabbitMQ check (Phase 3)
    # Try connect to RabbitMQ
    
    status_code = 200 if all_healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if all_healthy else "not_ready",
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
```

---

### **Endpoint 3: Liveness Check**

**Route:** `GET /health/live`

**Purpose:** Check if application process is alive (for Kubernetes)

**Response (200 OK):**
```json
{
  "status": "alive",
  "timestamp": "2026-06-22T10:30:00Z"
}
```

**Business Logic:**
- Always return 200 OK if process is running
- Kubernetes uses this to know if pod needs restart

---

## Task 2.6: Write Integration Tests

### File: `tests/integration/test_api.py`


### Test Suite Structure

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.api_gateway.main import app
from backend.shared.database import Base, get_db

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

---

### **Test 1: Authentication Flow**

```python
def test_register_and_login(client):
    # Register new user
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "role": "user"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "password" not in data
    
    # Login with credentials
    response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "TestPass123!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Get current user with token
    token = data["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"

def test_login_with_wrong_password(client):
    # Register user
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    
    # Try login with wrong password
    response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "WrongPassword"
    })
    assert response.status_code == 401

def test_duplicate_email_registration(client):
    # Register user
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    
    # Try to register again with same email
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "AnotherPass123!"
    })
    assert response.status_code == 409
```

---

### **Test 2: Activity CRUD Operations**

```python
def test_create_activity(client):
    # Register and login
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    login_response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "TestPass123!"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create activity
    activity_data = {
        "name": "TEST_ACTIVITY",
        "domain": "NOKIA",
        "description": "Test activity",
        "version": "1.0.0",
        "git_commit_sha": "abc123",
        "config": {
            "commands": [{"command_id": "CMD_001", "command": "show version"}],
            "authentication": {"type": "direct_ssh"},
            "state_data_map": {}
        }
    }
    response = client.post("/api/v1/activities", json=activity_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "TEST_ACTIVITY"
    assert data["is_active"] is True
    activity_id = data["id"]
    
    # Get activity
    response = client.get(f"/api/v1/activities/{activity_id}", headers=headers)
    assert response.status_code == 200
    
    # Update activity
    response = client.put(
        f"/api/v1/activities/{activity_id}",
        json={"description": "Updated description"},
        headers=headers
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Updated description"
    
    # List activities
    response = client.get("/api/v1/activities", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    
    # Delete activity
    response = client.delete(f"/api/v1/activities/{activity_id}", headers=headers)
    assert response.status_code == 200
    
    # Verify activity is deactivated
    response = client.get(f"/api/v1/activities/{activity_id}", headers=headers)
    assert response.json()["is_active"] is False
```

---

### **Test 3: Execution Creation**

```python
def test_create_execution(client):
    # Setup: Register, login, create activity
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    login_response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "TestPass123!"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    activity_data = {
        "name": "TEST_ACTIVITY",
        "domain": "NOKIA",
        "description": "Test",
        "version": "1.0.0",
        "git_commit_sha": "abc123",
        "config": {
            "commands": [{"command_id": "CMD_001", "command": "show version"}],
            "authentication": {"type": "direct_ssh"},
            "state_data_map": {}
        }
    }
    activity_response = client.post("/api/v1/activities", json=activity_data, headers=headers)
    activity_id = activity_response.json()["id"]
    
    # Create execution
    execution_data = {
        "activity_id": activity_id,
        "cr_id": "CR123456",
        "execution_mode": "parallel",
        "max_parallelism": 10,
        "input_data": {
            "nodes": [
                {
                    "node_name": "ROUTER01",
                    "node_ip": "10.20.30.40"
                }
            ]
        }
    }
    response = client.post("/api/v1/executions", json=execution_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "queued"
    assert data["cr_id"] == "CR123456"
    execution_id = data["id"]
    
    # Get execution details
    response = client.get(f"/api/v1/executions/{execution_id}", headers=headers)
    assert response.status_code == 200
    
    # List executions
    response = client.get("/api/v1/executions", headers=headers)
    assert response.status_code == 200
    assert response.json()["total"] == 1

def test_create_execution_with_invalid_activity(client):
    # Register and login
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    login_response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "TestPass123!"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to create execution with non-existent activity
    execution_data = {
        "activity_id": 9999,
        "cr_id": "CR123456",
        "execution_mode": "parallel",
        "max_parallelism": 10,
        "input_data": {"nodes": [{"node_name": "TEST", "node_ip": "1.1.1.1"}]}
    }
    response = client.post("/api/v1/executions", json=execution_data, headers=headers)
    assert response.status_code == 404
```

---

### **Test 4: Error Handling**

```python
def test_unauthorized_access(client):
    # Try to access protected endpoint without token
    response = client.get("/api/v1/activities")
    assert response.status_code == 401

def test_invalid_token(client):
    # Try to access with invalid token
    headers = {"Authorization": "Bearer invalid_token_here"}
    response = client.get("/api/v1/activities", headers=headers)
    assert response.status_code == 401

def test_get_nonexistent_activity(client):
    # Register and login
    client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!"
    })
    login_response = client.post("/api/v1/auth/login", data={
        "username": "test@example.com",
        "password": "TestPass123!"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get non-existent activity
    response = client.get("/api/v1/activities/9999", headers=headers)
    assert response.status_code == 404
```

---

## Running the Tests

```bash
# Install test dependencies
pip install pytest pytest-cov httpx

# Run all tests
pytest tests/integration/test_api.py -v

# Run with coverage
pytest tests/integration/test_api.py --cov=backend --cov-report=html

# Run specific test
pytest tests/integration/test_api.py::test_register_and_login -v
```

---

## Phase 2 Completion Checklist

- [ ] FastAPI application initialized with middleware
- [ ] CORS configured for frontend
- [ ] Exception handlers implemented
- [ ] JWT authentication working
- [ ] User registration endpoint implemented
- [ ] User login endpoint implemented
- [ ] Token refresh endpoint implemented
- [ ] Get current user endpoint implemented
- [ ] List activities endpoint with pagination and filters
- [ ] Create activity endpoint with validation
- [ ] Get activity details endpoint
- [ ] Update activity endpoint
- [ ] Delete/deactivate activity endpoint
- [ ] Start execution endpoint with validation
- [ ] List executions endpoint with filters
- [ ] Get execution details endpoint
- [ ] Get execution results endpoint
- [ ] Cancel execution endpoint
- [ ] Basic health check endpoint
- [ ] Readiness check endpoint with dependency checks
- [ ] Liveness check endpoint
- [ ] Integration tests for authentication flow
- [ ] Integration tests for activity CRUD
- [ ] Integration tests for execution creation
- [ ] Integration tests for error handling

---

## Next Steps (Phase 3)

After completing Phase 2, you will have a fully functional REST API with authentication. Phase 3 will add:

1. Celery integration for asynchronous task processing
2. RabbitMQ message publishing when executions are created
3. Worker processes to consume execution messages
4. Redis for result storage and caching

---

## Tips for AI Code Generation

When asking an AI tool to generate code for these endpoints:

1. **Provide the database models** - Share the User, Activity, Execution models
2. **Provide the schemas** - Share the Pydantic schemas for request/response
3. **Reference this document** - Point to specific endpoint sections
4. **Ask for one endpoint at a time** - Don't try to generate everything at once
5. **Request tests alongside code** - Ask for both implementation and tests
6. **Specify error handling** - Mention the error responses you need

### Example Prompts:

**Good Prompt:**
"Create the FastAPI endpoint for `POST /api/v1/activities` that creates a new activity. Use the Activity model from backend/models/activity.py and ActivityCreate schema. The endpoint should validate the config structure (must have commands, authentication, state_data_map), check for duplicate names, set created_by to current user ID, and return 201 with the created activity. Include error handling for 400 (invalid config) and 409 (duplicate name)."

**Bad Prompt:**
"Make an endpoint to create activities."

---

## Common Issues and Solutions

### Issue 1: JWT Token Not Being Validated
**Solution:** Ensure SECRET_KEY is loaded from environment variables and oauth2_scheme is properly configured.

### Issue 2: CORS Errors from Frontend
**Solution:** Add frontend URL to allow_origins in CORS middleware.

### Issue 3: Database Session Not Closing
**Solution:** Use `try/finally` block in get_db dependency to ensure session closes.

### Issue 4: Passwords Visible in API Responses
**Solution:** Use Pydantic schemas without password_hash field for responses.

### Issue 5: Pagination Not Working Correctly
**Solution:** Ensure skip = (page - 1) * page_size, not page * page_size.

---

**End of Phase 2 Detailed Specification**
