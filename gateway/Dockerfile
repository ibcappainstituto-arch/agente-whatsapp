FROM node:24-bookworm-slim
WORKDIR /app
COPY package.json ./
# Packages come only from canonical npm registry; no downloaded shell installer.
# First authorized build resolves transitive dependencies; lockfile is not shipped/tested.
RUN npm install --omit=dev --no-audit --no-fund && npm cache clean --force \
    && mkdir -p /data && chown node:node /data
COPY --chown=node:node server.mjs guard.mjs ./
USER node
ENV NODE_ENV=production DATA_DIR=/data
EXPOSE 3210
CMD ["node", "server.mjs"]
