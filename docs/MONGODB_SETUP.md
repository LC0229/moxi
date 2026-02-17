# MongoDB setup (learned from llm-twin-course)

## How llm-twin-course uses MongoDB

In **llm-twin-course**:

- **Default is local MongoDB** (Docker): `mongodb://mongo1:30001,mongo2:30002,mongo3:30003/?replicaSet=my-replica-set`
- Config keys: `MONGO_DATABASE_HOST`, `MONGO_DATABASE_NAME`
- They run `docker-compose` and connect to that local replica set — **no TLS**, no Atlas
- Connection: `MongoClient(settings.MONGO_DATABASE_HOST)` then `client[settings.MONGO_DATABASE_NAME]`

So when llm-twin-course “works,” it’s usually against **local Mongo in Docker**, not Atlas. That’s why you don’t see SSL issues there.

## Moxi: same pattern, two options

We use the same idea: `MongoClient(settings.MONGODB_URI)` and `client[settings.MONGODB_DB_NAME]`.

You can point at either:

### 1. Local MongoDB (recommended if you hit Atlas SSL errors)

Run Mongo via our docker-compose (no TLS):

```bash
docker compose up -d mongodb
```

In `.env`:

```env
MONGODB_URI=mongodb://moxi:moxi@localhost:27017
MONGODB_DB_NAME=moxi
```

Then your app and `scripts/test_mongo_connect.py` connect to local Mongo and avoid Atlas TLS entirely.

### 2. MongoDB Atlas

In `.env`:

```env
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB_NAME=moxi
```

On some Macs, Atlas can fail with `TLSV1_ALERT_INTERNAL_ERROR` (client OpenSSL vs Atlas TLS). If that happens, use local MongoDB above or run the app in Docker.

## Quick test

```bash
# With local Mongo (docker compose up -d mongodb + .env as above):
python scripts/test_mongo_connect.py
# Expect: OK: MongoDB ping succeeded.
```
