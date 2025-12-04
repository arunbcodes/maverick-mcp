# Web UI Configuration

How to configure the Maverick web dashboard.

## Environment Variables

Create a `.env.local` file in `apps/web/`:

```bash
# API URL (required)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Internal API URL for SSR (optional, defaults to NEXT_PUBLIC_API_URL)
API_URL=http://api:8000
```

### Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | - | Public API URL for browser requests |
| `API_URL` | No | Same as public | Internal API URL for server-side requests |
| `NEXT_PUBLIC_APP_NAME` | No | Maverick | Application name |

### Environment-Specific Configuration

#### Development (Local)

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Development (Docker)

```bash
# Set via docker-compose
NEXT_PUBLIC_API_URL=http://localhost:8000
API_URL=http://api:8000  # Internal Docker network
```

#### Production

```bash
# .env.production
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## next.config.js

The main Next.js configuration:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker
  output: 'standalone',

  // API proxy for development
  async rewrites() {
    return [
      {
        source: '/api/v1/:path*',
        destination: process.env.API_URL || 'http://localhost:8000/api/v1/:path*',
      },
    ];
  },

  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
  },

  // Image optimization
  images: {
    domains: ['localhost'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
};

module.exports = nextConfig;
```

### API Rewrites

The `rewrites` configuration proxies API requests in development:

- Browser requests to `/api/v1/*` are forwarded to the backend
- Avoids CORS issues during development
- In production, configure your reverse proxy instead

### Standalone Output

`output: 'standalone'` creates a minimal production build:

- Only includes necessary dependencies
- Smaller Docker images (~150MB vs ~500MB)
- Faster cold starts

## Styling Configuration

### Tailwind CSS

`tailwind.config.ts`:

```typescript
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Custom colors
        brand: {
          50: '#f0f9ff',
          // ... full palette
          900: '#0c4a6e',
        },
      },
      fontFamily: {
        sans: ['var(--font-geist-sans)'],
        mono: ['var(--font-geist-mono)'],
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
```

### CSS Variables

Global styles in `globals.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    /* ... more variables */
  }

  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    /* ... dark mode variables */
  }
}
```

## React Query Configuration

Data fetching is configured in `providers.tsx`:

```typescript
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      gcTime: 5 * 60 * 1000, // 5 minutes (formerly cacheTime)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

### Query Options

| Option | Value | Description |
|--------|-------|-------------|
| `staleTime` | 60s | Time before data is considered stale |
| `gcTime` | 5min | Time to keep inactive queries in cache |
| `retry` | 1 | Number of retry attempts on failure |
| `refetchOnWindowFocus` | false | Don't refetch when window gains focus |

### Adjusting for Your Needs

```typescript
// For real-time data (prices)
const { data } = useQuery({
  queryKey: ['stock', ticker],
  queryFn: () => fetchStockQuote(ticker),
  staleTime: 0, // Always fresh
  refetchInterval: 5000, // Poll every 5s
});

// For static data (company info)
const { data } = useQuery({
  queryKey: ['company', ticker],
  queryFn: () => fetchCompanyInfo(ticker),
  staleTime: 24 * 60 * 60 * 1000, // 24 hours
});
```

## Authentication Configuration

Authentication context in `lib/auth/auth-context.tsx`:

```typescript
interface AuthConfig {
  // API endpoints
  loginUrl: '/api/v1/auth/login';
  logoutUrl: '/api/v1/auth/logout';
  refreshUrl: '/api/v1/auth/refresh';
  meUrl: '/api/v1/auth/me';

  // Redirect paths
  loginRedirect: '/dashboard';
  logoutRedirect: '/login';

  // Token handling
  tokenStorageKey: 'auth_token';
  refreshTokenStorageKey: 'refresh_token';
}
```

### Protected Routes

Wrap protected pages with `ProtectedRoute`:

```typescript
// app/(dashboard)/layout.tsx
import { ProtectedRoute } from '@/components/auth/protected-route';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ProtectedRoute>{children}</ProtectedRoute>;
}
```

## Chart Configuration

Recharts configuration for consistent styling:

```typescript
// lib/chart-config.ts
export const chartConfig = {
  colors: {
    primary: '#3b82f6',
    secondary: '#10b981',
    negative: '#ef4444',
    grid: '#e5e7eb',
  },
  fonts: {
    family: 'var(--font-geist-sans)',
    size: 12,
  },
  margins: {
    top: 20,
    right: 20,
    bottom: 20,
    left: 60,
  },
};
```

## Build Configuration

### TypeScript

`tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Path Aliases

Import using `@/` prefix:

```typescript
import { Button } from '@/components/ui/button';
import { useStockQuote } from '@/lib/api/hooks';
```

## Runtime Configuration

For values that should be configurable at runtime (not build time):

```typescript
// lib/config.ts
export const config = {
  apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  appName: process.env.NEXT_PUBLIC_APP_NAME || 'Maverick',

  // Feature flags
  features: {
    darkMode: true,
    alerts: false, // Coming soon
    export: false, // Coming soon
  },

  // Limits
  maxTickersPerPriceStream: 50,
  maxApiKeysPerUser: 10,
};
```

## Docker Configuration

When running in Docker, configuration is passed via environment variables in `docker-compose.yml`:

```yaml
services:
  web:
    environment:
      - NODE_ENV=production
      - API_URL=http://api:8000
      - NEXT_PUBLIC_API_URL=http://localhost:8000
```

See [Docker Guide](../deployment/docker.md) for full Docker configuration.

## Troubleshooting

### API Connection Issues

1. Check `NEXT_PUBLIC_API_URL` is set correctly
2. Ensure API server is running
3. Check browser console for CORS errors
4. Verify network connectivity in Docker

### Build Errors

1. Clear `.next` directory: `rm -rf .next`
2. Clear node_modules: `rm -rf node_modules && npm install`
3. Check TypeScript errors: `npm run type-check`

### Styling Issues

1. Clear Tailwind cache: `rm -rf .next`
2. Check `tailwind.config.ts` content paths
3. Verify CSS imports in `globals.css`

## Next Steps

- [Development Guide](development.md) - Contributing to the UI
- [Docker Deployment](../deployment/docker.md) - Production setup

