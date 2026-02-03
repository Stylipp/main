FROM node:20-alpine AS build

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10 --activate

# Copy workspace root files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Copy only the frontend package.json for dependency install
COPY apps/stylipp.com/package.json apps/stylipp.com/

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy frontend source
COPY apps/stylipp.com/ apps/stylipp.com/

# Build
ARG VITE_API_URL=https://api.stylipp.com
ENV VITE_API_URL=${VITE_API_URL}
RUN cd apps/stylipp.com && pnpm build

# Production stage
FROM nginx:alpine

COPY apps/stylipp.com/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/apps/stylipp.com/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:80/ || exit 1
