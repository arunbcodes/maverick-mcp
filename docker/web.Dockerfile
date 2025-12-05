# Next.js Web Application
# Maverick Financial Analysis Dashboard
#
# Build: docker build -f docker/web.Dockerfile -t maverick-web:latest .
# Run:   docker run -p 3000:3000 maverick-web:latest

# --- Dependencies stage ---
FROM node:20-alpine AS deps

RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files
COPY apps/web/package.json apps/web/package-lock.json* ./

# Install dependencies
RUN npm ci --only=production=false

# --- Builder stage ---
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source code
COPY apps/web ./

# Build arguments for environment
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Build the application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# --- Runner stage ---
FROM node:20-alpine AS runner

LABEL maintainer="Maverick MCP"
LABEL description="Maverick Web Dashboard"

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs

# Copy public assets (create dir if empty)
COPY --from=builder /app/public ./public

# Set correct permissions for prerender cache
RUN mkdir .next \
    && chown nextjs:nodejs .next

# Copy standalone build
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/ || exit 1

# Start the server
CMD ["node", "server.js"]

