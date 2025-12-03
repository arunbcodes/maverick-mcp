# Architecture Decision Records (ADR)

This directory contains Architecture Decision Records for the MaverickMCP project.

## What is an ADR?

An Architecture Decision Record captures an important architectural decision made along with its context and consequences.

## ADR Index

| Number | Title | Status | Date |
|--------|-------|--------|------|
| [001](001-api-versioning.md) | API Versioning Strategy | Accepted | 2024-12-02 |
| [002](002-authentication-strategy.md) | Multi-Strategy Authentication | Accepted | 2024-12-02 |
| [003](003-shared-services-architecture.md) | Shared Services Architecture | Accepted | 2024-12-02 |
| [004](004-rate-limiting-strategy.md) | Tiered Rate Limiting | Accepted | 2024-12-02 |
| [005](005-sse-vs-websocket.md) | SSE vs WebSocket | Accepted | 2024-12-02 |

## ADR Template

```markdown
# ADR-XXX: Title

## Status

[Proposed | Accepted | Deprecated | Superseded by ADR-YYY]

## Date

YYYY-MM-DD

## Context

What is the issue that we're seeing that is motivating this decision?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

## Alternatives Considered

What other options were considered and why were they rejected?

## References

Links to relevant resources, documentation, or discussions.
```

## Statuses

- **Proposed**: Under discussion
- **Accepted**: Decided and will be implemented
- **Deprecated**: No longer relevant
- **Superseded**: Replaced by another ADR

## Creating a New ADR

1. Copy the template above
2. Number sequentially (006, 007, etc.)
3. Fill in all sections
4. Add to this README's index
5. Submit PR for review

