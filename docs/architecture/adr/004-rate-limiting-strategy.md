# ADR-004: Tiered Rate Limiting Strategy

## Status

Accepted

## Date

2024-12-02

## Context

We need to protect our API from abuse while providing fair access based on subscription tier. Additionally, some endpoints (AI research, backtesting) are expensive and need stricter limits.

## Decision

We will implement **tiered rate limiting** with **per-endpoint overrides**.

### Tier Limits

| Tier       | Requests/min | LLM Tokens/day | LLM Tokens/month |
|------------|--------------|----------------|------------------|
| Free       | 100          | 10,000         | 100,000          |
| Pro        | 1,000        | 100,000        | 1,000,000        |
| Enterprise | 10,000       | 1,000,000      | 10,000,000       |

### Endpoint-Specific Limits

Some endpoints have stricter limits regardless of tier:

```python
ENDPOINT_LIMITS = {
    "/api/v1/backtest/run": {"requests": 10, "window": 3600},      # 10/hour
    "/api/v1/research/analyze": {"requests": 20, "window": 3600},  # 20/hour
    "/api/v1/backtest/optimize": {"requests": 5, "window": 3600},  # 5/hour
}
```

### Implementation

**Algorithm**: Sliding window counter using Redis sorted sets

```python
async def check_limit(user_id: str, endpoint: str, limits: dict):
    key = f"rate_limit:{user_id}:{endpoint}"
    now = time.time()
    window = limits["window"]
    
    # Remove old entries
    await redis.zremrangebyscore(key, 0, now - window)
    
    # Count current requests
    current = await redis.zcard(key)
    
    if current >= limits["requests"]:
        raise HTTPException(429, "Rate limit exceeded")
    
    # Add current request
    await redis.zadd(key, {str(now): now})
    await redis.expire(key, window)
```

### Response Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1701532800
Retry-After: 60  (only on 429)
```

### LLM Token Budgets

Separate from request rate limits, we track LLM token usage:

```python
class LLMTokenBudget:
    async def check_budget(self, user_id: str, tier: str, tokens: int):
        daily_key = f"token_usage:{user_id}:daily"
        current = await redis.get(daily_key) or 0
        
        if current + tokens > TIER_BUDGETS[tier]["daily"]:
            raise HTTPException(429, "Daily token budget exceeded")
    
    async def record_usage(self, user_id: str, tokens: int):
        await redis.incrby(f"token_usage:{user_id}:daily", tokens)
```

## Consequences

### Positive
- Protects system from abuse
- Fair resource allocation by tier
- Expensive operations protected separately
- Clear feedback to users via headers

### Negative
- Requires Redis for distributed rate limiting
- Complexity in tracking multiple limits
- Must handle Redis failures gracefully

## Failure Mode

If Redis is unavailable, we **fail open** (allow requests) to avoid blocking all users. Logging alerts operations team.

## Alternatives Considered

1. **Fixed window counter**
   - Rejected: Allows burst at window boundaries

2. **Token bucket**
   - Rejected: More complex, sliding window sufficient

3. **In-memory rate limiting**
   - Rejected: Doesn't work with multiple API workers

## References

- [Rate Limiting Algorithms](https://konghq.com/blog/how-to-design-a-scalable-rate-limiting-algorithm)
- [Redis Rate Limiting](https://redis.io/commands/incr/#pattern-rate-limiter)

