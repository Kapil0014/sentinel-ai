# The image tag MUST match the "playwright" version pinned in package.json (currently 1.63.0),
# otherwise Playwright cannot find its browser build.
FROM mcr.microsoft.com/playwright:v1.63.0-noble

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json tsconfig.build.json ./
COPY src ./src
RUN npm run build && npm prune --omit=dev

# The Playwright image ships an unprivileged "pwuser".
USER pwuser
ENV NODE_ENV=production PORT=8081
EXPOSE 8081
CMD ["node", "dist/index.js"]
