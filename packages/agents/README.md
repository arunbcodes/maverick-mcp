# Maverick Agents

AI/LLM agent orchestration for Maverick stock analysis.

## Overview

This package provides:

- **Research Agents**: Deep financial research with web search and AI analysis
- **Market Agents**: Market analysis and stock screening agents
- **Supervisor Agent**: Multi-agent orchestration with LangGraph

## Installation

```bash
pip install maverick-agents
```

Or with uv:

```bash
uv add maverick-agents
```

## Features

### Research Agents
- Comprehensive financial research with multiple sources
- Company-specific deep dives
- Market sentiment analysis
- Source validation and credibility scoring

### Market Agents
- Technical analysis with AI interpretation
- Stock screening with persona-aware recommendations
- Pattern recognition and trend analysis

### Supervisor Agent
- Multi-agent coordination using LangGraph
- Intelligent task routing
- Results synthesis and aggregation

## Dependencies

- maverick-core: Core interfaces
- langchain: LLM framework
- langgraph: Multi-agent workflows
- anthropic/openai: LLM providers
- exa-py: Web search

## Configuration

Configure via environment variables:

- `ANTHROPIC_API_KEY`: Claude API key
- `OPENAI_API_KEY`: OpenAI API key
- `OPENROUTER_API_KEY`: OpenRouter API key
- `EXA_API_KEY`: Exa web search API key
