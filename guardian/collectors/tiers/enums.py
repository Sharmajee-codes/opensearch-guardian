"""Collection tier definitions per ADR-005."""

from enum import Enum


class Tier(str, Enum):
    """Collection tiers per ADR-005."""

    T1 = "t1"  # ~5s — cluster health, lightweight status
    T2 = "t2"  # ~10-15s — node metrics, shard state
    T3 = "t3"  # ~30-60s — index/storage statistics, recoveries
    T4 = "t4"  # ~5min — expensive diagnostics, mappings, policies
    T5 = "t5"  # on-demand — allocation explain, targeted diagnostics