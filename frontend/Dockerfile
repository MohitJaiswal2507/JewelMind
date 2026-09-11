# ==============================================================================
# JewelMind Frontend Dockerfile (Multi-Stage Production Build)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build React + Vite SPA
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency definitions
COPY package.json package-lock.json* ./

# Install dependencies deterministically
RUN npm ci

# Copy source code and build configurations
COPY tsconfig.json tsconfig.app.json* tsconfig.node.json* vite.config.ts index.html ./
COPY public/ ./public/
COPY src/ ./src/

# Build arguments for Vite environment injection
ARG VITE_API_URL=http://localhost:8000
ARG VITE_SUPABASE_URL=""
ARG VITE_SUPABASE_ANON_KEY=""

ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_SUPABASE_URL=${VITE_SUPABASE_URL}
ENV VITE_SUPABASE_ANON_KEY=${VITE_SUPABASE_ANON_KEY}

# Build optimized production static assets
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Static File Server (Nginx)
# ------------------------------------------------------------------------------
FROM nginx:1.27-alpine AS runner

# Remove default nginx configuration and html files
RUN rm -rf /etc/nginx/conf.d/default.conf /usr/share/nginx/html/*

# Copy custom high-performance nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose standard web port
EXPOSE 80

# Lightweight health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -q -O - http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
