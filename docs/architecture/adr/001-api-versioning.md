# ADR-001: API Versioning Strategy

## Status

Accepted

## Date

2024-12-02

## Context

We are building a REST API that will serve:
- Web applications
- Mobile applications (future)
- Programmatic access via API keys

We need a versioning strategy that allows API evolution without breaking existing clients.

## Decision

We will use **URL-based versioning** with the following pattern:

```
/api/v1/stocks/AAPL
/api/v2/stocks/AAPL  (future)
```

### Versioning Rules

1. **Major Version (v1 → v2)**: Breaking changes
   - Removing endpoints
   - Changing response structure
   - Removing required fields
   - Changing authentication mechanism

2. **No version bump needed for**:
   - Adding new endpoints
   - Adding optional fields to responses
   - Bug fixes
   - Performance improvements

3. **Deprecation Policy**:
   - 6-month notice before removing endpoints
   - `Sunset` header with deprecation date
   - `Deprecation` header with RFC 8594 format

### Implementation

```python
# Response headers for deprecated endpoints
Sunset: Sat, 01 Jun 2025 00:00:00 GMT
Deprecation: true
Link: </api/v2/stocks>; rel="successor-version"
```

## Consequences

### Positive
- Clients can migrate at their own pace
- Old versions remain functional during transition
- Clear communication of breaking changes

### Negative
- Server must maintain multiple versions (increased complexity)
- Documentation must cover all active versions

## Alternatives Considered

1. **Header-based versioning** (`Accept: application/vnd.maverick.v1+json`)
   - Rejected: Less discoverable, harder to test

2. **Query parameter versioning** (`?version=1`)
   - Rejected: Not RESTful, caching complications

3. **No versioning** (always backward compatible)
   - Rejected: Limits ability to evolve API

## References

- [API Versioning Best Practices](https://restfulapi.net/versioning/)
- [RFC 8594 - The Sunset HTTP Header](https://tools.ietf.org/html/rfc8594)

