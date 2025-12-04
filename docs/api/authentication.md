# Authentication

Maverick supports multiple authentication strategies to accommodate different client types.

## Authentication Methods

| Method | Best For | Security Level |
|--------|----------|----------------|
| **Cookie (HttpOnly)** | Web browsers | Highest |
| **JWT Bearer** | Mobile apps, SPAs | High |
| **API Key** | Scripts, integrations | Medium |

## Cookie Authentication (Web)

Best for traditional web applications with server-side session management.

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "user@example.com",
    "password": "your-password"
  }'
```

**Response:**

```json
{
  "message": "Login successful",
  "user": {
    "id": "usr_abc123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

The response sets an HttpOnly cookie:

```http
Set-Cookie: session=<session_id>; HttpOnly; Secure; SameSite=Lax; Path=/
```

### Making Authenticated Requests

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -b cookies.txt
```

### Logout

```bash
curl -X POST "http://localhost:8000/api/v1/auth/logout" \
  -b cookies.txt
```

### Security Features

- **HttpOnly**: Cookie not accessible via JavaScript (XSS protection)
- **Secure**: Only sent over HTTPS in production
- **SameSite=Lax**: CSRF protection
- **Session TTL**: 7 days (configurable)

## JWT Authentication (Mobile/SPA)

Best for mobile apps and single-page applications.

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -H "X-Auth-Method: jwt" \
  -d '{
    "email": "user@example.com",
    "password": "your-password"
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### Making Authenticated Requests

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Token Refresh

Access tokens expire after 15 minutes. Use the refresh token to get a new access token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

!!! note "Refresh Token Rotation"
    Each refresh request returns a new refresh token. The old refresh token is invalidated. This prevents token reuse attacks.

### Token Lifetimes

| Token | Lifetime | Storage Recommendation |
|-------|----------|------------------------|
| Access Token | 15 minutes | Memory only |
| Refresh Token | 7 days | Secure storage (Keychain, encrypted) |

### JWT Claims

```json
{
  "sub": "usr_abc123",
  "email": "user@example.com",
  "iat": 1705318200,
  "exp": 1705319100,
  "type": "access"
}
```

## API Key Authentication

Best for scripts, CI/CD, and server-to-server integrations.

### Create API Key

```bash
curl -X POST "http://localhost:8000/api/v1/api-keys" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline",
    "expires_in_days": 90
  }'
```

**Response:**

```json
{
  "id": "key_abc123",
  "name": "CI/CD Pipeline",
  "key": "mav_sk_abc123xyz789...",
  "key_prefix": "mav_sk_abc",
  "created_at": "2024-01-15T10:30:00Z",
  "expires_at": "2024-04-15T10:30:00Z"
}
```

!!! warning "Save Your Key"
    The full API key is only shown once at creation. Store it securely immediately.

### Using API Keys

```bash
curl -X GET "http://localhost:8000/api/v1/stocks/AAPL/quote" \
  -H "X-API-Key: mav_sk_abc123xyz789..."
```

### List API Keys

```bash
curl -X GET "http://localhost:8000/api/v1/api-keys" \
  -H "Authorization: Bearer <token>"
```

**Response:**

```json
{
  "data": [
    {
      "id": "key_abc123",
      "name": "CI/CD Pipeline",
      "key_prefix": "mav_sk_abc",
      "created_at": "2024-01-15T10:30:00Z",
      "expires_at": "2024-04-15T10:30:00Z",
      "last_used_at": "2024-01-16T08:00:00Z"
    }
  ]
}
```

### Revoke API Key

```bash
curl -X DELETE "http://localhost:8000/api/v1/api-keys/key_abc123" \
  -H "Authorization: Bearer <token>"
```

### API Key Security

- Keys are hashed before storage (only prefix stored in plain text)
- Keys can have expiration dates
- Keys track last usage time
- Keys can be revoked at any time

## User Registration

### Create Account

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecureP@ssw0rd!",
    "name": "John Doe"
  }'
```

**Response:**

```json
{
  "message": "Account created successfully",
  "user": {
    "id": "usr_abc123",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

## Password Management

### Change Password

```bash
curl -X PUT "http://localhost:8000/api/v1/auth/password" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldP@ssw0rd!",
    "new_password": "NewP@ssw0rd!"
  }'
```

### Password Hashing

Passwords are hashed using **Argon2id** (winner of the Password Hashing Competition):

- Memory: 64 MB
- Iterations: 3
- Parallelism: 4

## Security Best Practices

### For Web Applications

1. Use HttpOnly cookies (default for web)
2. Enable CSRF protection
3. Use HTTPS in production
4. Implement session timeout

### For Mobile/SPA

1. Store refresh tokens securely (Keychain, encrypted storage)
2. Keep access tokens in memory only
3. Implement token refresh before expiry
4. Handle 401 responses gracefully

### For API Keys

1. Use environment variables, never hardcode
2. Rotate keys periodically
3. Use shortest necessary expiration
4. Monitor last_used_at for anomalies
5. Revoke unused keys

## Error Responses

### 401 Unauthorized

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token"
  }
}
```

### 403 Forbidden

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions"
  }
}
```

## Architecture Decision

See [ADR-002: Authentication Strategy](../architecture/adr/002-authentication-strategy.md) for the rationale behind the multi-auth approach.

