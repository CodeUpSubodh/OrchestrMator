# OrchestrMator API - Quick Reference Card

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication Endpoints

### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "role": "user"
}
```

### Login
```http
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

---

## Activity Endpoints

### List Activities
```http
GET /activities?page=1&page_size=20&domain=NOKIA&is_active=true&search=precheck
Authorization: Bearer <access_token>
```

### Create Activity
```http
POST /activities
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "MPBN_PRECHECK",
  "domain": "NOKIA",
  "description": "Pre-check automation",
  "version": "1.0.0",
  "git_commit_sha": "abc123",
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
      "cr_id": ""
    }
  }
}
```

### Get Activity
```http
GET /activities/{id}
Authorization: Bearer <access_token>
```

### Update Activity
```http
PUT /activities/{id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "description": "Updated description",
  "version": "1.1.0"
}
```

### Delete Activity (Soft Delete)
```http
DELETE /activities/{id}
Authorization: Bearer <access_token>
```

---

## Execution Endpoints

### Start Execution
```http
POST /executions
Authorization: Bearer <access_token>
Content-Type: application/json

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
          "password": "encrypted"
        },
        "custom_params": {
          "region": "EAST"
        }
      }
    ],
    "global_params": {
      "maintenance_window": "2026-06-22 22:00-24:00"
    }
  }
}
```

### List Executions
```http
GET /executions?page=1&status=completed&activity_id=1&cr_id=CR123456
Authorization: Bearer <access_token>
```

### Get Execution Details
```http
GET /executions/{id}
Authorization: Bearer <access_token>
```

### Get Execution Results
```http
GET /executions/{id}/results?node_name=ROUTER01&include_commands=true
Authorization: Bearer <access_token>
```

### Cancel Execution
```http
DELETE /executions/{id}
Authorization: Bearer <access_token>
```

---

## Health Endpoints

### Basic Health Check
```http
GET /health
```

### Readiness Check
```http
GET /health/ready
```

### Liveness Check
```http
GET /health/live
```

---

## Common Response Codes

| Code | Meaning | When It Happens |
|------|---------|----------------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST (resource created) |
| 400 | Bad Request | Invalid input data or structure |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., email already exists) |
| 422 | Unprocessable Entity | Validation error (Pydantic) |
| 503 | Service Unavailable | Health check failed |

---

## Data Models Quick Reference

### User
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

### Activity (Minimal)
```json
{
  "id": 1,
  "name": "MPBN_PRECHECK",
  "domain": "NOKIA",
  "description": "Pre-check automation",
  "version": "1.0.0",
  "is_active": true,
  "created_by": 1,
  "created_at": "2026-06-22T10:30:00Z"
}
```

### Execution (Minimal)
```json
{
  "id": 1,
  "activity_id": 1,
  "cr_id": "CR123456",
  "status": "queued",
  "execution_mode": "parallel",
  "max_parallelism": 10,
  "created_at": "2026-06-22T10:30:00Z",
  "created_by": 1
}
```

---

## Execution Modes

| Mode | Description | Max Parallelism Used? |
|------|-------------|----------------------|
| `sequential` | Execute nodes one at a time | No |
| `parallel` | Execute all nodes simultaneously | Yes |
| `batch` | Group nodes into batches | Yes |

---

## Execution Statuses

| Status | Description |
|--------|-------------|
| `queued` | Execution created, waiting to start |
| `running` | Currently executing |
| `completed` | All nodes finished successfully |
| `partial_success` | Some nodes failed |
| `failed` | Execution failed completely |
| `cancelled` | User cancelled execution |

---

## Node Result Statuses

| Status | Description |
|--------|-------------|
| `success` | Node completed successfully |
| `failed` | Node execution failed |
| `skipped` | Node was skipped (conditional logic) |
| `timeout` | Node execution timed out |

---

## Curl Examples

### Register and Get Token
```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"Pass123!"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=user@example.com&password=Pass123!"

# Save token
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Create Activity
```bash
curl -X POST http://localhost:8000/api/v1/activities \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### List Activities
```bash
curl http://localhost:8000/api/v1/activities?page=1&page_size=10 \
  -H "Authorization: Bearer $TOKEN"
```

### Start Execution
```bash
curl -X POST http://localhost:8000/api/v1/executions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "activity_id": 1,
    "cr_id": "CR123456",
    "execution_mode": "parallel",
    "max_parallelism": 10,
    "input_data": {
      "nodes": [
        {"node_name": "ROUTER01", "node_ip": "10.20.30.40"}
      ]
    }
  }'
```

---

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Register and login
def get_token():
    # Register
    requests.post(f"{BASE_URL}/auth/register", json={
        "email": "user@example.com",
        "password": "Pass123!"
    })
    
    # Login
    response = requests.post(f"{BASE_URL}/auth/login", data={
        "username": "user@example.com",
        "password": "Pass123!"
    })
    return response.json()["access_token"]

# Create activity
def create_activity(token):
    headers = {"Authorization": f"Bearer {token}"}
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
    response = requests.post(f"{BASE_URL}/activities", json=activity_data, headers=headers)
    return response.json()

# Start execution
def start_execution(token, activity_id):
    headers = {"Authorization": f"Bearer {token}"}
    execution_data = {
        "activity_id": activity_id,
        "cr_id": "CR123456",
        "execution_mode": "parallel",
        "max_parallelism": 10,
        "input_data": {
            "nodes": [{"node_name": "ROUTER01", "node_ip": "10.20.30.40"}]
        }
    }
    response = requests.post(f"{BASE_URL}/executions", json=execution_data, headers=headers)
    return response.json()

# Usage
token = get_token()
activity = create_activity(token)
execution = start_execution(token, activity["id"])
print(f"Execution ID: {execution['id']}, Status: {execution['status']}")
```

---

## Testing with httpie

```bash
# Install httpie
pip install httpie

# Register
http POST http://localhost:8000/api/v1/auth/register \
  email=user@example.com password=Pass123!

# Login
http POST http://localhost:8000/api/v1/auth/login \
  username=user@example.com password=Pass123!

# List activities (with token)
http GET http://localhost:8000/api/v1/activities \
  Authorization:"Bearer $TOKEN"
```

---

**For detailed specifications, see [PHASE_2_API_GATEWAY_DETAILED.md](./PHASE_2_API_GATEWAY_DETAILED.md)**
