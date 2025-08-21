# OpenASP DevOps - Optimized Multi-stage Docker build
FROM node:18-alpine AS base

# Install security updates and necessary packages
RUN apk update && apk upgrade && \
    apk add --no-cache libc6-compat dumb-init curl && \
    rm -rf /var/cache/apk/*

# Create non-root user early
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Install dependencies only when needed
FROM base AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies with cache optimization
RUN --mount=type=cache,target=/root/.npm \
  if [ -f package-lock.json ]; then \
    npm ci --only=production --ignore-scripts --no-audit --no-fund; \
  else \
    echo "Lockfile not found." && exit 1; \
  fi

# Install dev dependencies for build
FROM base AS dev-deps
WORKDIR /app
COPY package.json package-lock.json* ./

RUN --mount=type=cache,target=/root/.npm \
  if [ -f package-lock.json ]; then \
    npm ci --ignore-scripts --no-audit --no-fund; \
  else \
    echo "Lockfile not found." && exit 1; \
  fi

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app

# Copy dev dependencies for build
COPY --from=dev-deps /app/node_modules ./node_modules

# Copy source code (use .dockerignore to exclude unnecessary files)
COPY . .

# Environment variables for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build application with optimization
RUN --mount=type=cache,target=/app/.next/cache \
    npm run build && \
    npm prune --production && \
    rm -rf .git .github tests docs *.md && \
    rm -rf node_modules/.cache

# Production image - minimal and secure
FROM base AS runner
WORKDIR /app

# Production environment variables
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3016
ENV HOSTNAME="0.0.0.0"

# Copy only production dependencies
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules

# Copy built application
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Create .next directory with correct permissions
RUN mkdir -p .next && \
    chown -R nextjs:nodejs .next && \
    chmod -R 755 .next

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3016

# Health check with improved reliability
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:3016/api/health || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]

# Add labels for better maintainability
LABEL org.opencontainers.image.title="OpenASP DevOps" \
      org.opencontainers.image.description="Legacy System Modernization DevOps Platform" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="OpenASP AX" \
      org.opencontainers.image.licenses="Proprietary"