# Maverick Web UI

A modern web interface for the Maverick stock analysis platform built with Next.js 14+.

## Features

- **Authentication**: Email/password login with JWT tokens and automatic refresh
- **Dashboard**: Portfolio overview with real-time P&L tracking
- **Stock Screener**: Find stocks using Maverick's AI-powered screening
- **Portfolio Management**: Track positions and performance

## Tech Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **State Management**: Zustand + React Query
- **Components**: Custom components inspired by shadcn/ui

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm (recommended) or npm
- Running Maverick API backend

### Installation

```bash
# From the monorepo root
pnpm install

# Or from this directory
pnpm install
```

### Development

```bash
# Start the development server
pnpm dev

# The app will be available at http://localhost:3000
```

Make sure the Maverick API is running at `http://localhost:8000` (or configure `API_URL` in `.env.local`).

### Building

```bash
pnpm build
pnpm start
```

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── (auth)/            # Auth pages (login, register)
│   ├── (dashboard)/       # Protected dashboard pages
│   └── page.tsx           # Landing page
├── components/
│   ├── auth/              # Auth-related components
│   ├── ui/                # Reusable UI components
│   └── providers.tsx      # App-wide providers
└── lib/
    ├── api/               # API client with token refresh
    ├── auth/              # Auth context and hooks
    └── utils.ts           # Utility functions
```

## Environment Variables

Copy `.env.example` to `.env.local` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_URL` | Backend API URL (server-side proxy) | `http://localhost:8000` |
| `NEXT_PUBLIC_API_URL` | Public API URL (optional) | - |

## API Integration

The web app uses a BFF (Backend for Frontend) pattern:
- API requests go through Next.js rewrites to the backend
- JWT tokens are stored in localStorage
- Automatic token refresh on 401 responses
- Cookie-based sessions also supported for web clients

## Contributing

1. Follow the existing code style
2. Use TypeScript strictly
3. Add appropriate types for API responses
4. Test authentication flows thoroughly

