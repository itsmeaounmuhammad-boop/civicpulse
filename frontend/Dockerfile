FROM node:22-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build


FROM nginx:1.29-alpine3.23 AS runtime

# Base-image tags lag behind Alpine's rolling security patches (see PR discussion /
# ENGINEERING-NOTES). Upgrading here picks up whatever is newest in the pinned
# Alpine 3.23 repo at build time, instead of waiting on the next nginx image rebuild.
RUN apk update && apk upgrade --no-cache

COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist /usr/share/nginx/html

USER nginx
EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD ["wget", "-q", "-O", "/dev/null", "http://127.0.0.1:8080/healthz"]

CMD ["nginx", "-g", "daemon off;"]