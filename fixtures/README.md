# OpenSearch Fixture Environments

Fixture environments are self-contained Docker Compose stacks that create
reproducible cluster states for development and testing.

## Quick Start

```sh
# Healthy cluster — green health, single node
docker compose -f deploy/docker/fixtures/healthy/docker-compose.yml up -d
curl http://localhost:9200/_cluster/health
# → { "status": "green", ... }

# Broken cluster — degraded state for Doctor rule testing
docker compose -f deploy/docker/fixtures/broken/docker-compose.yml up -d
docker compose -f deploy/docker/fixtures/broken/docker-compose.yml run --rm seed
curl http://localhost:9201/_cluster/health
```

## Fixtures

### `healthy/`
Single-node OpenSearch cluster in demo mode. No TLS, no authentication.
- Port: **9200**
- Node name: `osg-node1`
- Cluster name: `osg-cluster-healthy`
- JVM heap: 512 MB
- Persistent volume: `healthy-node1-data`

**Tests exercised:** basic health check, node list, shard allocation,
index statistics, JVM stats.

### `broken/`
Single-node OpenSearch cluster deliberately degraded to reproduce common
operational problems:

| Degraded Condition | How It Is Created | Doctor Rule Target |
|--------------------|-------------------|--------------------|
| Disk high watermark | Watermark set to 95% (normal: 85%) | `disk-watermark-high` |
| JVM heap pressure | Heap limited to 128 MB | `jvm-heap-pressure` |
| Unassigned shards / oversharding | 20 indices × 5 shards = 100 shards in a 128 MB heap | `excessive-shard-density` |
| High indexing load | 5 000-document bulk after seeding | `thread-pool-rejections` |

- Port: **9201**
- Node name: `osg-broken-node`
- Cluster name: `osg-cluster-broken`
- Seed container: runs once to create indices and fill data, then exits

## Stopping Fixtures

```sh
docker compose -f deploy/docker/fixtures/healthy/docker-compose.yml down -v
docker compose -f deploy/docker/fixtures/broken/docker-compose.yml down -v
```

The `-v` flag removes persistent volumes. Omit it to preserve data between
restarts.
