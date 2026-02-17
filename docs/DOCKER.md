# Docker — What runs and when

Moxi uses Docker only for **infrastructure services**. App code runs on your host (e.g. `make moxi-collect`, `make moxi-chunk`).

## Services (docker-compose.yml)

| Service   | Image              | Ports      | Use |
|----------|--------------------|------------|-----|
| **mongodb** | mongo:7           | 27017      | Store collected READMEs and samples. Used by `moxi-collect`, `moxi-chunk`, pipeline dashboard. |
| **qdrant**  | qdrant/qdrant    | 6333, 6334 | Vector DB for RAG (optional; not used in collect → chunk → train). |
| **rabbitmq**| rabbitmq:3-management | 5672, 15672 | Message queue (optional; batch pipelines don’t use it yet). |

## Commands

```bash
# Start only what you need (e.g. MongoDB for collection)
docker compose up -d mongodb

# Or start everything
make docker-up

# Logs
make docker-logs   # or: docker compose logs -f mongodb

# Stop
make docker-down
```

## When to use Docker

- **MongoDB:** Use when you run `make moxi-collect` and want samples in Mongo (or use JSON-only and skip Docker).
- **Qdrant / RabbitMQ:** Only if you add RAG or async workers later; not required for the current moxi collect → chunk → train flow.

See `.env` for `MONGODB_URI` and `MONGODB_DB_NAME` when using MongoDB.
