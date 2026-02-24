# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM node:22-alpine AS base
ARG SVC_SLUG

# Install dependencies only when needed
FROM base AS deps
ARG SVC_SLUG
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY ./libs /app/libs
COPY ./services/${SVC_SLUG}/package.json /app/libs/package.json

RUN npm install -g npm@latest

WORKDIR /app/libs
RUN for dir in */; do \
    if [ -f $dir/package.json ]; then \
        relevant_deps=$(grep -o "file:.*/libs/${dir%/}" ./package.json); \
        if [ $? -eq 0 ]; then \
            cd $dir && \
            echo "Building dependency lib $relevant_deps" && \
            if [ -f yarn.lock ]; then yarn run build; \
            # TODO: For production, sync build vs. deploy NPM environment, generate package-lock.json, then change "npm install" to "npm ci"
            elif [ -f package-lock.json ]; then npm install; npm run build; \
            elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm run build; \
            else echo "Lockfile not found in $dir." && exit 1; \
            fi; \
            cd ..; \
        else \
            echo "Skipping dependency lib file:../../libs/${dir%/}"; \
        fi; \
    fi; \
  done

WORKDIR /app

COPY ./services/${SVC_SLUG}/package.json ./services/${SVC_SLUG}/yarn.lock* ./services/${SVC_SLUG}/package-lock.json* ./services/${SVC_SLUG}/pnpm-lock.yaml* ./

# Re-write local lib path.
RUN sed -i 's/file:\.\.\/\.\.\//file:/' ./package.json
RUN sed -i 's/file:\.\.\/\.\.\//file:/' ./package-lock.json
RUN sed -i 's/"\.\.\/\.\.\/libs/"libs/' ./package-lock.json

RUN \
  if [ -f yarn.lock ]; then yarn --frozen-lockfile; \
  # TODO: For production, sync build vs. deploy NPM environment, generate package-lock.json, then change "npm install" to "npm ci"
  elif [ -f package-lock.json ]; then npm install; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm i --frozen-lockfile; \
  else echo "Lockfile not found." && exit 1; \
  fi


# Debug
#RUN npm list


# Rebuild the source code only when needed
FROM base AS builder
ARG SVC_SLUG

# NextJS Build Vars
ARG NEXT_PUBLIC_APP_TITLE
ARG NEXT_PUBLIC_APP_DESCRIPTION
ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID
ARG NEXT_PUBLIC_BOT_INTRO_MESSAGE
ARG NEXT_PUBLIC_AGENT_ENGINE_URL
ARG NEXT_PUBLIC_AGENT_NAME
ARG NEXT_PUBLIC_AGENT_DESCRIPTION

ENV NEXT_PUBLIC_APP_TITLE=$NEXT_PUBLIC_APP_TITLE
ENV NEXT_PUBLIC_APP_DESCRIPTION=$NEXT_PUBLIC_APP_DESCRIPTION
ENV NEXT_PUBLIC_GOOGLE_CLIENT_ID=$NEXT_PUBLIC_GOOGLE_CLIENT_ID
ENV NEXT_PUBLIC_BOT_INTRO_MESSAGE=$NEXT_PUBLIC_BOT_INTRO_MESSAGE
ENV NEXT_PUBLIC_AGENT_ENGINE_URL=$NEXT_PUBLIC_AGENT_ENGINE_URL
ENV NEXT_PUBLIC_AGENT_NAME=$NEXT_PUBLIC_AGENT_NAME
ENV NEXT_PUBLIC_AGENT_DESCRIPTION=$NEXT_PUBLIC_AGENT_DESCRIPTION

WORKDIR /app
COPY --from=deps /app/libs ./libs
COPY --from=deps /app/node_modules ./node_modules
#COPY ./services/${SVC_SLUG}/. .

COPY services/${SVC_SLUG}/app.json ./
COPY services/${SVC_SLUG}/next.config.js ./
COPY services/${SVC_SLUG}/package*.json ./
COPY services/${SVC_SLUG}/tsconfig.json ./
COPY services/${SVC_SLUG}/postcss.config.mjs ./
COPY services/${SVC_SLUG}/tailwind.config.ts ./
COPY services/${SVC_SLUG}/app/ ./app/
COPY services/${SVC_SLUG}/components/ ./components/
COPY services/${SVC_SLUG}/public/ ./public/
COPY services/${SVC_SLUG}/services/ ./services/
COPY services/${SVC_SLUG}/styles/ ./styles/
COPY services/${SVC_SLUG}/types/ ./types/

# Re-write local lib path.
RUN sed -i 's/file:\.\.\/\.\.\//file:/' ./package.json
RUN sed -i 's/file:\.\.\/\.\.\//file:/' ./package-lock.json
RUN sed -i 's/"\.\.\/\.\.\/libs/"libs/' ./package-lock.json

# Next.js collects completely anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line in case you want to disable telemetry during the build.
# ENV NEXT_TELEMETRY_DISABLED 1

RUN npm install -g npm@latest


# Debug
#RUN npm config list
RUN npm list

# Uncomment to build TypeScript
RUN \
  if [ -f yarn.lock ]; then yarn run build; \
  elif [ -f package-lock.json ]; then npm run build; \
  elif [ -f pnpm-lock.yaml ]; then corepack enable pnpm && pnpm run build; \
  else echo "Lockfile not found." && exit 1; \
  fi

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
# Uncomment the following line in case you want to disable telemetry during runtime.
# ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
#COPY --from=deps /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

#COPY --from=deps --chown=nextjs:nodejs /app/.next/standalone ./
#COPY --from=deps --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 8080

ENV PORT=8080

# server.js is created by next build from the standalone output
# https://nextjs.org/docs/pages/api-reference/next-config-js/output
CMD HOSTNAME="0.0.0.0" node server.js
