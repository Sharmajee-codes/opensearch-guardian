# OpenSearch Guardian

Open-source desktop operations console for OpenSearch — monitoring, Cluster Doctor, cost optimizer, and safe provisioning.

## Overview

Guardian connects to existing OpenSearch clusters, continuously monitors cluster health, diagnoses operational problems, identifies observability cost and capacity opportunities, and optionally provisions or scales nodes through Docker or Kubernetes.

For the full specification, see [docs/SOP.md](docs/SOP.md).

## Features

- Live cluster monitoring (health, nodes, JVM, CPU, memory, disk, shards, recoveries)
- Deterministic Cluster Doctor with evidence-backed diagnosis
- Observability Cost Optimizer for retention, storage, shard, and capacity inefficiencies
- Guided node provisioning and scaling with preflight checks and verification
- Read-only by default; write/provisioning requires explicit approval per connection
- Works with bare-metal, VM, Docker, and Kubernetes deployments — no proprietary backend required

## Getting Started

See [docs/SOP.md](docs/SOP.md) for the full setup and architecture guide.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Apache License 2.0 — see [LICENSE](LICENSE).
