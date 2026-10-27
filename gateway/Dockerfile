FROM node:24-bookworm-slim
WORKDIR /app
COPY package.json package-lock.json ./
# Packages come only from canonical npm registry; no downloaded shell installer.
# Lockfile was installed/import-tested on Windows; this optional Docker build remains untested.
RUN npm ci --ignore-scripts --omit=dev --registry=https://registry.npmjs.org --no-audit --no-fund && npm cache clean --force \
    && mkdir -p /data && chown node:node /data
COPY --chown=node:node server.mjs guard.mjs disconnect-diagnostic.mjs qr-lifecycle.mjs qr-frame.mjs ./
USER node
ENV NODE_ENV=production DATA_DIR=/data
EXPOSE 3210
CMD ["node", "server.mjs"]
