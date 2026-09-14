FROM node:22-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
COPY backend/package.json backend/package.json
COPY frontend/package.json frontend/package.json
RUN npm ci
COPY backend backend
COPY frontend frontend
COPY assets assets

FROM dependencies AS web-build
RUN npm run build

FROM node:22-alpine AS api
ENV NODE_ENV=production
WORKDIR /app
COPY package.json package-lock.json ./
COPY backend/package.json backend/package.json
COPY frontend/package.json frontend/package.json
RUN npm ci --omit=dev --workspace=@estoque/api && npm cache clean --force
COPY backend backend
USER node
EXPOSE 3000
CMD ["node", "backend/src/server.js"]

FROM nginx:stable-alpine AS web
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=web-build /app/frontend/dist /usr/share/nginx/html
EXPOSE 80
