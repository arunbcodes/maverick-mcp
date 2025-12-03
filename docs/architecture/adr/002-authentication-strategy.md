# ADR-002: Multi-Strategy Authentication

## Status

Accepted

## Date

2024-12-02

## Context

We need to support multiple client types with different authentication requirements:

1. **Web Application**: Browser-based, needs CSRF protection
2. **Mobile Application**: Native apps, needs refresh token rotation
3. **Programmatic Access**: Scripts/integrations, needs simple auth

## Decision

We will implement a **multi-strategy authentication system** with three methods:

### 1. Cookie Authentication (Web)

```
POST /api/v1/auth/login
→ Set-Cookie: maverick_session=xxx; HttpOnly; Secure; SameSite=Lax
→ Set-Cookie: maverick_csrf=yyy; Secure; SameSite=Strict
```

**Security Features:**
- HttpOnly session cookie (prevents XSS access)
- Secure flag (HTTPS only)
- SameSite=Lax (prevents CSRF for GET)
- CSRF token for mutations (double-submit cookie pattern)

**CSRF Protection:**
```javascript
// Frontend must read CSRF cookie and send in header
fetch('/api/v1/portfolio/positions', {
  method: 'POST',
  credentials: 'include',
  headers: { 'X-CSRF-Token': getCookie('maverick_csrf') }
});
```

### 2. JWT Authentication (Mobile)

```
POST /api/v1/auth/login
→ { "access_token": "xxx", "refresh_token": "yyy" }

GET /api/v1/stocks/AAPL
Authorization: Bearer xxx
```

**Security Features:**
- Short-lived access tokens (15 minutes)
- Long-lived refresh tokens (30 days)
- Refresh token rotation (single-use)
- Token reuse detection → invalidate all tokens

**Refresh Token Rotation:**
```
POST /api/v1/auth/refresh
{ "refresh_token": "old_token" }
→ { "access_token": "new_access", "refresh_token": "new_refresh" }
```

### 3. API Key Authentication (Programmatic)

```
GET /api/v1/stocks/AAPL
X-API-Key: mav_live_xxxxxxxxxxxxx
```

**Features:**
- Simple header-based auth
- Per-key rate limits
- Usage tracking
- Revocable

## Middleware Order

```
Request → CORS → Logging → Auth → Rate Limit → Handler
```

Auth middleware tries strategies in order:
1. Cookie (check session cookie)
2. JWT (check Authorization header)
3. API Key (check X-API-Key header)

First successful auth wins.

## Consequences

### Positive
- Each client type uses optimal auth method
- Security best practices for each context
- Single codebase, multiple auth methods

### Negative
- More complex than single auth method
- Must maintain three auth implementations
- Testing requires coverage of all methods

## Alternatives Considered

1. **JWT only for all clients**
   - Rejected: Poor security for web (XSS can steal tokens)

2. **OAuth 2.0 with external provider**
   - Rejected: Overkill for personal use, adds external dependency

3. **Session-based only**
   - Rejected: Doesn't work well for mobile/programmatic access

## Security Considerations

1. **Cookie theft**: HttpOnly prevents JS access
2. **CSRF attacks**: Double-submit cookie pattern
3. **Token theft (mobile)**: Short-lived tokens limit damage
4. **Token reuse**: Detected and all tokens invalidated
5. **API key compromise**: Keys are revocable, usage tracked

## References

- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
- [JWT Best Practices](https://auth0.com/blog/jwt-validation-guide/)
- [Refresh Token Rotation](https://auth0.com/docs/secure/tokens/refresh-tokens/refresh-token-rotation)

