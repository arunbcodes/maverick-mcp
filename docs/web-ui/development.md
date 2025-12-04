# Web UI Development

Guide to developing and contributing to the Maverick web dashboard.

## Getting Started

### Prerequisites

- Node.js 20+
- npm 10+
- Running backend (API server)

### Setup

```bash
# Navigate to web app
cd apps/web

# Install dependencies
npm install

# Start development server
npm run dev

# Open in browser
open http://localhost:3000
```

### With Docker Backend

```bash
# Start backend services
make docker-backend

# Run web locally (faster hot-reload)
cd apps/web
npm run dev
```

## Project Structure

```
apps/web/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/            # Auth pages (login, register)
│   │   │   ├── layout.tsx
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (dashboard)/       # Protected pages
│   │   │   ├── layout.tsx     # Dashboard layout with sidebar
│   │   │   ├── dashboard/page.tsx
│   │   │   ├── portfolio/page.tsx
│   │   │   ├── screener/page.tsx
│   │   │   ├── settings/page.tsx
│   │   │   └── stocks/
│   │   │       └── [ticker]/page.tsx
│   │   ├── globals.css        # Global styles
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Landing page
│   │
│   ├── components/            # React components
│   │   ├── auth/             # Auth-related components
│   │   ├── portfolio/        # Portfolio components
│   │   ├── providers.tsx     # Context providers
│   │   └── ui/               # shadcn/ui components
│   │
│   └── lib/                   # Utilities and hooks
│       ├── api/              # API client and hooks
│       │   ├── client.ts     # Fetch wrapper
│       │   ├── hooks/        # React Query hooks
│       │   └── types.ts      # TypeScript types
│       ├── auth/             # Auth context
│       └── utils.ts          # Helper functions
│
├── public/                    # Static assets
├── next.config.js            # Next.js config
├── tailwind.config.ts        # Tailwind config
├── tsconfig.json             # TypeScript config
└── package.json
```

## Component Architecture

### UI Components (`components/ui/`)

Based on [shadcn/ui](https://ui.shadcn.com/), these are unstyled, accessible primitives:

```typescript
// components/ui/button.tsx
import { cva, type VariantProps } from 'class-variance-authority';

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md text-sm font-medium',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground',
        outline: 'border border-input bg-background hover:bg-accent',
        // ...
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
      },
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    />
  );
}
```

### Feature Components

Domain-specific components combining UI primitives:

```typescript
// components/portfolio/position-row.tsx
export function PositionRow({ position, onEdit, onDelete }: PositionRowProps) {
  const { data: quote } = useStockQuote(position.ticker);
  const priceStream = usePriceStream([position.ticker]);

  const currentPrice = priceStream[position.ticker]?.price ?? quote?.price;
  const pnl = currentPrice ? (currentPrice - position.avg_cost) * position.shares : 0;

  return (
    <TableRow>
      <TableCell>{position.ticker}</TableCell>
      <TableCell>{position.shares}</TableCell>
      <TableCell>{formatCurrency(position.avg_cost)}</TableCell>
      <TableCell>{formatCurrency(currentPrice)}</TableCell>
      <TableCell className={pnl >= 0 ? 'text-green-600' : 'text-red-600'}>
        {formatCurrency(pnl)}
      </TableCell>
      <TableCell>
        <Button variant="ghost" size="sm" onClick={() => onEdit(position)}>
          Edit
        </Button>
      </TableCell>
    </TableRow>
  );
}
```

## Data Fetching

### React Query Hooks

All API calls are wrapped in custom hooks:

```typescript
// lib/api/hooks/use-portfolio.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';

export function usePortfolio() {
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: () => apiClient.get('/portfolio'),
  });
}

export function useAddPosition() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AddPositionRequest) =>
      apiClient.post('/portfolio/positions', data),
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['portfolio'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
    },
  });
}
```

### Using Hooks in Components

```typescript
function PortfolioPage() {
  const { data: portfolio, isLoading, error } = usePortfolio();
  const addPosition = useAddPosition();

  if (isLoading) return <LoadingState />;
  if (error) return <ErrorState error={error} />;

  const handleAdd = async (data: AddPositionRequest) => {
    await addPosition.mutateAsync(data);
    toast.success('Position added');
  };

  return (
    <div>
      <PortfolioSummary data={portfolio} />
      <AddPositionForm onSubmit={handleAdd} isLoading={addPosition.isPending} />
    </div>
  );
}
```

### SSE Hooks

For real-time data:

```typescript
// lib/api/hooks/use-sse.ts
export function usePriceStream(tickers: string[]) {
  const [prices, setPrices] = useState<Record<string, PriceUpdate>>({});

  useEffect(() => {
    if (tickers.length === 0) return;

    const eventSource = new EventSource(
      `/api/v1/sse/prices?tickers=${tickers.join(',')}`
    );

    eventSource.addEventListener('price', (event) => {
      const data = JSON.parse(event.data);
      setPrices((prev) => ({ ...prev, [data.ticker]: data }));
    });

    return () => eventSource.close();
  }, [tickers.join(',')]);

  return prices;
}
```

## Styling

### Tailwind CSS

Use Tailwind utilities for styling:

```tsx
<div className="flex items-center gap-4 p-4 bg-card rounded-lg shadow-sm">
  <span className="text-2xl font-bold text-foreground">{price}</span>
  <span className={cn(
    'text-sm',
    change >= 0 ? 'text-green-600' : 'text-red-600'
  )}>
    {formatPercent(change)}
  </span>
</div>
```

### CSS Variables

Theme colors use CSS variables:

```css
/* Light mode */
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 222.2 47.4% 11.2%;
}

/* Dark mode */
.dark {
  --background: 222.2 84% 4.9%;
  --foreground: 210 40% 98%;
}
```

### Component Styling

Use the `cn()` utility for conditional classes:

```typescript
import { cn } from '@/lib/utils';

function Card({ className, variant, ...props }) {
  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-6',
        variant === 'elevated' && 'shadow-lg',
        className
      )}
      {...props}
    />
  );
}
```

## Forms

### React Hook Form + Zod

```typescript
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  ticker: z.string().min(1, 'Ticker is required'),
  shares: z.number().positive('Shares must be positive'),
  price: z.number().positive('Price must be positive'),
  date: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

function AddPositionForm({ onSubmit }) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Input {...register('ticker')} error={errors.ticker?.message} />
      <Input
        type="number"
        {...register('shares', { valueAsNumber: true })}
        error={errors.shares?.message}
      />
      <Button type="submit">Add Position</Button>
    </form>
  );
}
```

## Testing

### Unit Tests

```bash
# Run tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage
```

### Component Tests

```typescript
import { render, screen } from '@testing-library/react';
import { PositionRow } from './position-row';

describe('PositionRow', () => {
  it('renders position data', () => {
    render(
      <PositionRow
        position={{ ticker: 'AAPL', shares: 10, avg_cost: 150 }}
        onEdit={jest.fn()}
        onDelete={jest.fn()}
      />
    );

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();
  });
});
```

## Code Quality

### Linting

```bash
# ESLint
npm run lint

# Fix auto-fixable issues
npm run lint -- --fix
```

### Type Checking

```bash
npm run type-check
```

### Formatting

```bash
# Prettier
npm run format
```

## Adding New Features

### 1. Create the API Hook

```typescript
// lib/api/hooks/use-new-feature.ts
export function useNewFeature(id: string) {
  return useQuery({
    queryKey: ['new-feature', id],
    queryFn: () => apiClient.get(`/new-feature/${id}`),
  });
}
```

### 2. Create the Component

```typescript
// components/new-feature/new-feature-card.tsx
export function NewFeatureCard({ id }: { id: string }) {
  const { data, isLoading } = useNewFeature(id);

  if (isLoading) return <Skeleton />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>{data.title}</CardTitle>
      </CardHeader>
      <CardContent>{data.content}</CardContent>
    </Card>
  );
}
```

### 3. Create the Page

```typescript
// app/(dashboard)/new-feature/page.tsx
export default function NewFeaturePage() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">New Feature</h1>
      <NewFeatureCard id="default" />
    </div>
  );
}
```

### 4. Add to Navigation

Update the sidebar in `layout.tsx`:

```typescript
const navigation = [
  // ...existing items
  { name: 'New Feature', href: '/new-feature', icon: StarIcon },
];
```

## Best Practices

### Do's

- ✅ Use TypeScript strictly
- ✅ Create custom hooks for data fetching
- ✅ Use loading and error states
- ✅ Validate forms with Zod
- ✅ Use semantic HTML
- ✅ Add ARIA labels for accessibility

### Don'ts

- ❌ Fetch data directly in components
- ❌ Store sensitive data in localStorage
- ❌ Use inline styles (use Tailwind)
- ❌ Ignore TypeScript errors
- ❌ Skip error handling

## Deployment

### Build

```bash
npm run build
```

### Docker

```bash
# Build image
docker build -f docker/web.Dockerfile -t maverick-web .

# Run container
docker run -p 3000:3000 maverick-web
```

See [Docker Guide](../deployment/docker.md) for full deployment instructions.

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Query Documentation](https://tanstack.com/query)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Components](https://ui.shadcn.com/)
- [Recharts Documentation](https://recharts.org/)

