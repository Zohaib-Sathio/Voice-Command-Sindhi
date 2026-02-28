# Authentication and Rate Limiting Implementation Plan

## Overview

This document outlines the implementation plan for adding user authentication, JWT-based API access, and per-user rate limiting to the FastAPI FortVoice API. The system will track API usage per user per day using a combination of MySQL (persistent storage) and Redis (caching layer) for optimal performance.

---

## Implementation Order

### Phase 1: Database Schema Setup
1. Create `users` table
2. Create `user_usage` table with composite index
3. Run database migrations

### Phase 2: Core Helper Modules
1. Create `day_helper.py` - Date utility functions
2. Create `jwt.py` - JWT token creation and validation
3. Create `redis.py` - Redis connection and usage caching
4. Update `db_functions.py` - Add user and usage management functions

### Phase 3: Database Actions Layer
1. Create `db_actions.py` - Business logic for usage tracking (Redis + DB coordination)

### Phase 4: API Endpoints
1. Create JWT generation endpoint (with API_KEY and IP locking)
2. Create JWT validation endpoint (public)
3. Update voice command endpoint with authentication middleware

### Phase 5: Middleware Integration
1. Create authentication middleware
2. Create usage checking middleware
3. Integrate middleware into voice command endpoint

---

## Database Schema

### Table 1: `users`
Stores user information and creation timestamps.

```sql
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
```

**Fields:**
- `user_id` (VARCHAR(255), PRIMARY KEY): Unique identifier for the user (e.g., API key or username)
- `created_at` (DATETIME): Timestamp when the user was created

### Table 2: `user_usage`
Tracks daily API usage per user with composite index for efficient queries.

```sql
CREATE TABLE user_usage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    day DATE NOT NULL,
    usage_count INT DEFAULT 0 NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_user_day (user_id, day),
    INDEX idx_user_day (user_id, day)
);
```

**Fields:**
- `id` (INT, PRIMARY KEY, AUTO_INCREMENT): Auto-incrementing primary key
- `user_id` (VARCHAR(255), FOREIGN KEY): References `users.user_id`
- `day` (DATE): Date in format YYYY-MM-DD (e.g., 2025-01-03)
- `usage_count` (INT): Number of API calls made by the user on this day
- **Composite Index**: `(user_id, day)` for fast lookups and uniqueness constraint

**Index Strategy:**
- Composite index `(user_id, day)` ensures:
  - Fast queries for specific user-day combinations
  - Uniqueness constraint (one record per user per day)
  - Efficient updates and inserts

---

## Module Specifications

### 1. `day_helper.py`
Utility module for date operations.

**Location:** `src/utils/day_helper.py`

**Functions:**
```python
def get_current_day() -> str:
    """
    Returns the current date in YYYY-MM-DD format.
    
    Returns:
        str: Current date as string (e.g., "2025-01-03")
    
    Example:
        >>> get_current_day()
        "2025-01-03"
    """
```

**Implementation Notes:**
- Use `datetime.date.today()` to get current date
- Format as `YYYY-MM-DD` string
- Ensure timezone consistency (use UTC if needed)

---

### 2. `jwt.py`
JWT token creation and validation module.

**Location:** `src/utils/jwt.py`

**Dependencies:**
- `PyJWT` library (add to `requirements.txt`)
- Secret key from environment variables

**Functions:**

```python
def create_jwt(user_id: str) -> str:
    """
    Creates a JWT token for a user with expiration.
    
    Args:
        user_id (str): The user identifier
    
    Returns:
        str: JWT token string
    
    Implementation:
        - Include user_id in token payload
        - Set expiration time (e.g., 24 hours, 7 days, or configurable)
        - Sign with secret key from environment
        - Return encoded token
    """
```

```python
def validate_jwt(token: str) -> str | None:
    """
    Validates a JWT token and returns the user_id if valid.
    
    Args:
        token (str): JWT token string
    
    Returns:
        str | None: user_id if token is valid, None otherwise
    
    Implementation:
        - Decode token using secret key
        - Verify expiration
        - Verify signature
        - Return user_id from payload if valid
        - Return None if invalid/expired
    """
```

**Configuration:**
- JWT secret key: `JWT_SECRET_KEY` (environment variable)
- Token expiration: `JWT_EXPIRATION_HOURS` (environment variable, default: 24)

**Error Handling:**
- Handle expired tokens
- Handle invalid signatures
- Handle malformed tokens

---

### 3. `redis.py`
Redis connection and usage caching module.

**Location:** `src/services/redis.py`

**Dependencies:**
- `redis` library (add to `requirements.txt`)

**Functions:**

```python
def get_redis_client():
    """
    Creates and returns a Redis client connection.
    
    Returns:
        redis.Redis: Redis client instance
    
    Configuration:
        - Host: REDIS_HOST (env var, default: localhost)
        - Port: REDIS_PORT (env var, default: 6379)
        - Password: REDIS_PASSWORD (env var, optional)
        - DB: REDIS_DB (env var, default: 0)
    """
```

```python
def set_usage(user_id: str, day: str, count: int) -> bool:
    """
    Sets the usage count for a user on a specific day in Redis.
    
    Args:
        user_id (str): User identifier
        day (str): Date in YYYY-MM-DD format
        count (int): Usage count to set
    
    Returns:
        bool: True if successful, False otherwise
    
    Redis Key Format:
        usage:{user_id}:{day}
        Example: usage:mubashir_ali:2025-01-03
    
    TTL:
        - Set expiration to end of day + buffer (e.g., 25 hours)
        - Ensures cache doesn't persist beyond the day
    """
```

```python
def get_usage(user_id: str, day: str) -> int | None:
    """
    Gets the usage count for a user on a specific day from Redis.
    
    Args:
        user_id (str): User identifier
        day (str): Date in YYYY-MM-DD format
    
    Returns:
        int | None: Usage count if found, None if not in cache
    
    Redis Key Format:
        usage:{user_id}:{day}
    """
```

**Redis Key Naming Convention:**
- Pattern: `usage:{user_id}:{day}`
- Example: `usage:mubashir_ali:2025-01-03`
- Value: Integer (usage count)

---

### 4. Database Functions (`db_functions.py`)

**Location:** `src/database/db_functions.py` (extend existing file)

**New Functions:**

```python
def create_user(db: Session, user_id: str) -> dict:
    """
    Creates a new user in the database.
    
    Args:
        db (Session): SQLAlchemy database session
        user_id (str): User identifier
    
    Returns:
        dict: Result dictionary with success status and message
    
    Implementation:
        - Check if user already exists
        - If not, insert new user record
        - Return success/error response
    """
```

```python
def get_user(db: Session, user_id: str) -> dict | None:
    """
    Retrieves a user from the database.
    
    Args:
        db (Session): SQLAlchemy database session
        user_id (str): User identifier
    
    Returns:
        dict | None: User data if found, None otherwise
    """
```

```python
def add_usage(db: Session, user_id: str, day: str, count: int) -> dict:
    """
    Adds usage count for a user on a specific day.
    
    Args:
        db (Session): SQLAlchemy database session
        user_id (str): User identifier
        day (str): Date in YYYY-MM-DD format
        count (int): Usage count to add
    
    Returns:
        dict: Result dictionary with success status
    
    Implementation:
        - Insert new record with usage_count = count
        - Or update existing record by incrementing usage_count
    """
```

```python
def update_usage(db: Session, user_id: str, day: str, count: int) -> dict:
    """
    Updates the usage count for a user on a specific day.
    
    Args:
        db (Session): SQLAlchemy database session
        user_id (str): User identifier
        day (str): Date in YYYY-MM-DD format
        count (int): New usage count value
    
    Returns:
        dict: Result dictionary with success status
    """
```

```python
def get_usage(db: Session, user_id: str, day: str) -> int:
    """
    Gets the usage count for a user on a specific day from the database.
    
    Args:
        db (Session): SQLAlchemy database session
        user_id (str): User identifier
        day (str): Date in YYYY-MM-DD format
    
    Returns:
        int: Usage count (0 if no record exists)
    """
```

**Database Schema Models:**

Add to `src/database/schema.py`:

```python
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String(255), primary_key=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class UserUsage(Base):
    __tablename__ = "user_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    day = Column(Date, nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('user_id', 'day', name='unique_user_day'),
        Index('idx_user_day', 'user_id', 'day'),
    )
```

---

### 5. `db_actions.py`
Business logic layer that coordinates between Redis cache and MySQL database.

**Location:** `src/database/db_actions.py`

**Functions:**

```python
def add_usage(user_id: str, day: str, current_usage: int) -> dict:
    """
    Adds usage for a user on a specific day.
    Coordinates between database and Redis cache.
    
    Args:
        user_id (str): User identifier
        day (str): Date in YYYY-MM-DD format
        current_usage (int): Current usage count to set
    
    Returns:
        dict: Result dictionary with success status
    
    Flow:
        1. Check if usage record exists in database for this user-day
        2. If record exists (usage_count > 0):
           - Call db.update_usage(user_id, day, current_usage)
        3. If record doesn't exist (usage_count == 0 or no record):
           - Call db.add_usage(user_id, day, current_usage)
        4. Update Redis cache: redis.set_usage(user_id, day, current_usage)
        5. Return success response
    
    Note:
        - This function ensures database and Redis stay in sync
        - Redis acts as a fast cache layer
        - Database is the source of truth
    """
```

```python
def get_usage(user_id: str, day: str) -> int:
    """
    Gets usage count for a user on a specific day.
    Checks Redis first, falls back to database if not in cache.
    
    Args:
        user_id (str): User identifier
        day (str): Date in YYYY-MM-DD format
    
    Returns:
        int: Usage count (0 if no record exists)
    
    Flow:
        1. Try to get from Redis: redis.get_usage(user_id, day)
        2. If found in Redis:
           - Return the cached value
        3. If not in Redis:
           - Query database: db.get_usage(user_id, day)
           - Cache the result in Redis: redis.set_usage(user_id, day, count)
           - Return the database value
    
    Cache Strategy:
        - Redis provides fast lookups for frequently accessed data
        - Database is queried only on cache miss
        - Cache is populated after database query for future requests
    """
```

**Synchronous Wrappers:**

For compatibility with existing code that uses `run_in_threadpool`:

```python
def sync_add_usage(user_id: str, day: str, current_usage: int) -> dict:
    """Synchronous wrapper for add_usage. Creates its own DB session."""

def sync_get_usage(user_id: str, day: str) -> int:
    """Synchronous wrapper for get_usage. Creates its own DB session."""
```

---

## API Endpoints

### 1. JWT Generation Endpoint

**Route:** `POST /v1/api/auth/generate-token`

**Purpose:** Generate JWT token for a user with API_KEY authentication and IP locking.

**Request:**
```json
{
    "api_key": "user_provided_api_key",
    "user_id": "mubashir_ali"  // Optional, can be derived from API_KEY
}
```

**Headers:**
- `X-Forwarded-For` or client IP for IP locking (optional)

**Flow:**
1. Extract `api_key` from request body
2. Extract client IP address from request
3. Validate API_KEY (can be against a whitelist or database)
4. Determine `user_id` (from API_KEY or request body)
5. Check if user exists: `db.get_user(user_id)`
6. If user doesn't exist (returns None):
   - Create new user: `db.create_user(user_id)`
7. If user exists:
   - Do nothing (user already exists)
8. Generate JWT token: `jwt.create_jwt(user_id)`
9. Return response with token

**Response (200 OK):**
```json
{
    "success": true,
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user_id": "mubashir_ali",
    "expires_in": 86400
}
```

**Error Responses:**
- `400 Bad Request`: Invalid API_KEY or missing parameters
- `401 Unauthorized`: Invalid API_KEY
- `500 Internal Server Error`: Database or JWT generation error

**IP Locking:**
- Store IP address associated with the API_KEY (optional enhancement)
- Can be stored in database or validated against whitelist
- For MVP, can be logged for audit purposes

---

### 2. JWT Validation Endpoint (Public)

**Route:** `GET /v1/api/auth/validate-token`

**Purpose:** Public endpoint to validate a JWT token.

**Request Headers:**
```
Authorization: Bearer <token>
```

**Flow:**
1. Extract token from `Authorization` header
2. Validate token: `jwt.validate_jwt(token)`
3. Return appropriate response

**Response (200 OK) - Valid Token:**
```json
{
    "valid": true,
    "user_id": "mubashir_ali",
    "message": "Token is valid"
}
```

**Response (401 Unauthorized) - Invalid/Expired Token:**
```json
{
    "valid": false,
    "message": "Token is invalid or expired"
}
```

**Error Handling:**
- Missing Authorization header → 401
- Invalid token format → 401
- Expired token → 401
- Invalid signature → 401

---

### 3. Voice Command Endpoint (Updated)

**Route:** `POST /v1/api/transcribe/command` (existing endpoint)

**Changes:**
- Add authentication middleware
- Add usage checking middleware
- Track usage after successful API call

**Request Headers:**
```
Authorization: Bearer <token>
```

**Middleware Flow:**
1. **Authentication Middleware:**
   - Extract token from `Authorization` header
   - Validate token: `jwt.validate_jwt(token)`
   - If invalid → Return 401 Unauthorized
   - If valid → Extract `user_id` and attach to request

2. **Usage Check Middleware:**
   - Get `user_id` from request (set by auth middleware)
   - Get current day: `day_helper.get_current_day()`
   - Get current usage: `db_actions.get_usage(user_id, day)`
   - Get user's daily limit (from database or configuration)
   - If `current_usage >= limit`:
     - Return 429 Too Many Requests
   - If `current_usage < limit`:
     - Attach usage info to request
     - Proceed to endpoint handler

3. **Endpoint Handler:**
   - Execute existing voice command logic
   - On successful completion:
     - Increment usage: `db_actions.add_usage(user_id, day, current_usage + 1)`

**Response (429 Too Many Requests):**
```json
{
    "error": "Rate limit exceeded",
    "message": "Daily API limit reached. Please try again tomorrow.",
    "limit": 100,
    "current_usage": 100
}
```

---

## Middleware Implementation

### Authentication Middleware

**Location:** `src/middleware/auth_middleware.py`

**Function:**
```python
async def authenticate_request(request: Request, call_next):
    """
    FastAPI middleware to authenticate requests using JWT tokens.
    
    Flow:
        1. Check if endpoint requires authentication (skip public endpoints)
        2. Extract token from Authorization header
        3. Validate token using jwt.validate_jwt()
        4. If valid: attach user_id to request.state
        5. If invalid: return 401 response
        6. Call next middleware/endpoint
    """
```

**Usage:**
- Apply to all protected endpoints
- Skip for public endpoints (e.g., `/health`, `/v1/api/auth/validate-token`)

### Usage Check Middleware

**Location:** `src/middleware/usage_middleware.py`

**Function:**
```python
async def check_usage_limit(request: Request, call_next):
    """
    FastAPI middleware to check and enforce usage limits.
    
    Flow:
        1. Get user_id from request.state (set by auth middleware)
        2. Get current day
        3. Get current usage from db_actions.get_usage()
        4. Get user's daily limit (from config or database)
        5. If usage >= limit: return 429 response
        6. If usage < limit: proceed to endpoint
        7. After endpoint execution: increment usage
    """
```

**Note:**
- Usage increment should happen after successful API call
- Use FastAPI's `BackgroundTasks` or response callback to increment usage
- Ensure atomic operations to prevent race conditions

---

## Configuration

### Environment Variables

Add to `.env` file:

```env
# JWT Configuration
JWT_SECRET_KEY=your_secret_key_here_min_32_chars
JWT_EXPIRATION_HOURS=24

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# API Rate Limits
DEFAULT_DAILY_LIMIT=100
```

### Docker Compose Updates

Update `docker-compose.yml` to include Redis service:

```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: fortvoice-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - fortvoice-network
    restart: unless-stopped

  app:
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis

volumes:
  redis_data:
```

---

## Data Flow Examples

### Example 1: First API Call of the Day

1. User sends request with JWT token
2. Auth middleware validates token → `user_id = "mubashir_ali"`
3. Usage middleware checks Redis → Not found
4. Usage middleware checks database → Not found (returns 0)
5. Usage middleware caches 0 in Redis
6. Usage < limit → Proceed to endpoint
7. Endpoint processes request successfully
8. After response: `db_actions.add_usage("mubashir_ali", "2025-01-03", 1)`
   - Database: Creates new record with `usage_count = 1`
   - Redis: Sets `usage:mubashir_ali:2025-01-03 = 1`

### Example 2: Subsequent API Calls

1. User sends request with JWT token
2. Auth middleware validates token → `user_id = "mubashir_ali"`
3. Usage middleware checks Redis → Found `usage:mubashir_ali:2025-01-03 = 5`
4. Usage < limit → Proceed to endpoint
5. Endpoint processes request successfully
6. After response: `db_actions.add_usage("mubashir_ali", "2025-01-03", 6)`
   - Database: Updates existing record to `usage_count = 6`
   - Redis: Updates `usage:mubashir_ali:2025-01-03 = 6`

### Example 3: Rate Limit Exceeded

1. User sends request with JWT token
2. Auth middleware validates token → `user_id = "mubashir_ali"`
3. Usage middleware checks Redis → Found `usage:mubashir_ali:2025-01-03 = 100`
4. Usage >= limit (100) → Return 429 Too Many Requests
5. Endpoint is not called

---

## Database Migration Strategy

### Option 1: SQLAlchemy Auto-Migration
- Use `Base.metadata.create_all()` in `init_db()` function
- Run migration script on deployment

### Option 2: Manual SQL Scripts
- Create SQL migration scripts
- Run manually or via migration tool

### Migration Script Location
- `src/database/migration.py` (extend existing file)

---

## Testing Considerations

### Unit Tests
- Test JWT creation and validation
- Test Redis get/set operations
- Test database CRUD operations
- Test `db_actions` coordination logic

### Integration Tests
- Test JWT generation endpoint
- Test JWT validation endpoint
- Test voice command endpoint with authentication
- Test rate limiting behavior
- Test cache invalidation

### Edge Cases
- Token expiration during request
- Redis connection failure (fallback to database)
- Database connection failure
- Concurrent requests (race conditions)
- Day boundary transitions (midnight)

---

## Security Considerations

1. **JWT Secret Key:**
   - Use strong, randomly generated secret key
   - Store in environment variables, never in code
   - Rotate periodically

2. **API Key Validation:**
   - Validate API_KEY against whitelist or database
   - Implement IP whitelisting if needed
   - Log all token generation attempts

3. **Rate Limiting:**
   - Prevent abuse with per-user limits
   - Consider implementing burst limits
   - Monitor for suspicious patterns

4. **Token Security:**
   - Use HTTPS in production
   - Set appropriate expiration times
   - Consider refresh token mechanism for long-lived sessions

---

## Performance Considerations

1. **Redis Caching:**
   - Reduces database load for frequent lookups
   - Set appropriate TTL to prevent stale data
   - Handle Redis failures gracefully (fallback to database)

2. **Database Indexing:**
   - Composite index on `(user_id, day)` ensures fast queries
   - Monitor query performance

3. **Connection Pooling:**
   - Use connection pooling for both MySQL and Redis
   - Configure appropriate pool sizes

---

## Dependencies to Add

Update `requirements.txt`:

```
PyJWT==2.8.0
redis==5.0.1
```

---

## Implementation Checklist

- [ ] Phase 1: Database Schema
  - [ ] Create `users` table
  - [ ] Create `user_usage` table with composite index
  - [ ] Add SQLAlchemy models to `schema.py`
  - [ ] Run database migration

- [ ] Phase 2: Core Helper Modules
  - [ ] Create `day_helper.py`
  - [ ] Create `jwt.py` with create/validate functions
  - [ ] Create `redis.py` with connection and get/set functions
  - [ ] Update `db_functions.py` with user and usage functions

- [ ] Phase 3: Database Actions Layer
  - [ ] Create `db_actions.py` with add_usage and get_usage
  - [ ] Implement Redis + DB coordination logic

- [ ] Phase 4: API Endpoints
  - [ ] Create JWT generation endpoint
  - [ ] Create JWT validation endpoint
  - [ ] Update voice command endpoint with auth

- [ ] Phase 5: Middleware Integration
  - [ ] Create authentication middleware
  - [ ] Create usage checking middleware
  - [ ] Integrate middleware into FastAPI app

- [ ] Phase 6: Configuration & Deployment
  - [ ] Add environment variables
  - [ ] Update docker-compose.yml with Redis
  - [ ] Update requirements.txt
  - [ ] Test end-to-end flow

---

## Notes

- **Day Format:** Always use `YYYY-MM-DD` format (e.g., "2025-01-03")
- **Timezone:** Consider using UTC for consistency across timezones
- **Atomic Operations:** Ensure usage increments are atomic to prevent race conditions
- **Error Handling:** Implement comprehensive error handling for all database and Redis operations
- **Logging:** Add appropriate logging for authentication, usage tracking, and errors
- **Monitoring:** Consider adding metrics for usage patterns and rate limit hits

---

## Questions to Resolve

1. **API Key Source:** Where will API keys come from? (Database, environment variables, external service?)
2. **Daily Limit:** Should limits be per-user configurable or global?
3. **Token Expiration:** What should be the default JWT expiration time?
4. **IP Locking:** Should IP addresses be stored and validated, or just logged?
5. **Rate Limit Response:** Should we include retry-after header in 429 responses?
6. **Usage Reset:** Should usage reset at midnight UTC or user's local timezone?

---

## Next Steps

1. Review this document with the team
2. Resolve open questions
3. Begin implementation in the order specified
4. Test each phase before moving to the next
5. Deploy to staging environment for testing
6. Monitor and adjust based on real-world usage patterns

