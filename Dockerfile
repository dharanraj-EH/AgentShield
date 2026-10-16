FROM node:22-slim AS dashboard
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend ./
RUN npm run build
FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY policies ./policies
COPY --from=dashboard /frontend/dist ./static
RUN useradd --create-home labuser && mkdir -p /data && chown -R labuser:labuser /app /data
USER labuser
ENV AGENTSHIELD_CONTAINER=1
ENV AGENTSHIELD_DB=sqlite:////tmp/agentshield.db
CMD ["python", "-m", "backend.container_start"]
