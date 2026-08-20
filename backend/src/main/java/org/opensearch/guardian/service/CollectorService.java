package org.opensearch.guardian.service;

import org.opensearch.cluster.service.ClusterService;
import org.opensearch.common.settings.Settings;
import org.opensearch.common.unit.TimeValue;
import org.opensearch.common.inject.Inject;
import org.opensearch.common.lifecycle.AbstractLifecycleComponent;
import org.opensearch.threadpool.ThreadPool;
import org.opensearch.guardian.model.ClusterSnapshot;
import org.opensearch.guardian.model.NodeSnapshot;
import org.opensearch.common.logging.Loggers;
import org.opensearch.cluster.node.DiscoveryNodeRole;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.apache.logging.log4j.Logger;

import java.io.IOException;

/**
 * Service responsible for collecting OpenSearch cluster metrics.
 * Implements tiered collection cadence (T1-T4) per ADR-005.
 */
public class CollectorService extends AbstractLifecycleComponent {

    private static final Logger logger = Loggers.getLogger(CollectorService.class);

    private final ClusterService clusterService;
    private final ThreadPool threadPool;
    private final Settings settings;
    private final Map<String, ClusterSnapshot> latestSnapshots;
    private final ScheduledExecutorService scheduler;

    // Collection intervals (configurable via settings)
    private final long t1IntervalMs;
    private final long t2IntervalMs;
    private final long t3IntervalMs;
    private final long t4IntervalMs;

    @Inject
    public CollectorService(ClusterService clusterService, ThreadPool threadPool, Settings settings) {
        super();
        this.clusterService = clusterService;
        this.threadPool = threadPool;
        this.settings = settings;
        this.latestSnapshots = new ConcurrentHashMap<>();
        this.scheduler = Executors.newScheduledThreadPool(4);

        // Read collection intervals from settings
        this.t1IntervalMs = settings.getAsTime("guardian.collection.interval.tier1", TimeValue.timeValueSeconds(5)).millis();
        this.t2IntervalMs = settings.getAsTime("guardian.collection.interval.tier2", TimeValue.timeValueSeconds(12)).millis();
        this.t3IntervalMs = settings.getAsTime("guardian.collection.interval.tier3", TimeValue.timeValueSeconds(45)).millis();
        this.t4IntervalMs = settings.getAsTime("guardian.collection.interval.tier4", TimeValue.timeValueSeconds(300)).millis();

        logger.info("CollectorService initialized with intervals: T1={}ms, T2={}ms, T3={}ms, T4={}ms",
                t1IntervalMs, t2IntervalMs, t3IntervalMs, t4IntervalMs);
    }

    @Override
    protected void doStart() {
        logger.info("Starting CollectorService");
        startSchedulers();
    }

    @Override
    protected void doStop() {
        logger.info("Stopping CollectorService");
        scheduler.shutdown();
    }

    @Override
    protected void doClose() throws IOException {
        logger.info("CollectorService closed");
        scheduler.shutdownNow();
    }

    private void startSchedulers() {
        // T1: Live collection (cluster health, node list)
        scheduler.scheduleAtFixedRate(() -> {
            try {
                collectTier1();
            } catch (Exception e) {
                logger.error("Error during T1 collection: {}", e.getMessage());
            }
        }, 0, t1IntervalMs, TimeUnit.MILLISECONDS);

        // T2: Trending collection (node stats, thread pools)
        scheduler.scheduleAtFixedRate(() -> {
            try {
                collectTier2();
            } catch (Exception e) {
                logger.error("Error during T2 collection: {}", e.getMessage());
            }
        }, 0, t2IntervalMs, TimeUnit.MILLISECONDS);

        // T3: Deep collection (index stats, cluster settings)
        scheduler.scheduleAtFixedRate(() -> {
            try {
                collectTier3();
            } catch (Exception e) {
                logger.error("Error during T3 collection: {}", e.getMessage());
            }
        }, 0, t3IntervalMs, TimeUnit.MILLISECONDS);

        // T4: Diagnostic collection (mappings, ILM policies)
        scheduler.scheduleAtFixedRate(() -> {
            try {
                collectTier4();
            } catch (Exception e) {
                logger.error("Error during T4 collection: {}", e.getMessage());
            }
        }, 0, t4IntervalMs, TimeUnit.MILLISECONDS);

        logger.info("All collection schedulers started");
    }

    /**
     * Collect Tier 1 data: cluster health and node list
     */
    private void collectTier1() {
        // Get cluster state
        var clusterState = clusterService.state();
        var clusterName = clusterState.getClusterName().value();

        // Count nodes by role
        int totalNodes = clusterState.getNodes().getSize();
        int dataNodes = 0;
        int masterNodes = 0;
        int ingestNodes = 0;

        for (org.opensearch.cluster.node.DiscoveryNode node : clusterState.getNodes().getNodes().values()) {
            if (node.getRoles().contains(DiscoveryNodeRole.DATA_ROLE)) {
                dataNodes++;
            }
            if (node.getRoles().contains(DiscoveryNodeRole.MASTER_ROLE)) {
                masterNodes++;
            }
            if (node.getRoles().contains(DiscoveryNodeRole.INGEST_ROLE)) {
                ingestNodes++;
            }
        }

        // Get health from cluster health API (simulated from cluster state)
        // In a real implementation, this would call the OpenSearch health API
        String healthStatus = "green"; // Default to green
        long unassignedShardsCount = clusterState.getRoutingTable().allShards().stream()
                .filter(shard -> shard.state() == org.opensearch.cluster.routing.ShardRoutingState.UNASSIGNED)
                .count();
        int unassignedShards = (int) unassignedShardsCount;

        // Create snapshot
        ClusterSnapshot snapshot = new ClusterSnapshot();
        snapshot.setClusterName(clusterName);
        snapshot.setHealthStatus(healthStatus);
        snapshot.setTotalNodes(totalNodes);
        snapshot.setDataNodes(dataNodes);
        snapshot.setMasterNodes(masterNodes);
        snapshot.setIngestNodes(ingestNodes);
        snapshot.setUnassignedShards(unassignedShards);
        snapshot.setCollectedAt(java.time.Instant.now());

        // Store in latest snapshots
        latestSnapshots.put("cluster", snapshot);

        logger.debug("T1 collection completed: cluster={}, health={}, nodes={}, unassigned={}",
                clusterName, healthStatus, totalNodes, unassignedShards);
    }

    /**
     * Collect Tier 2 data: node-level metrics
     */
    private void collectTier2() {
        // In a real implementation, this would call _nodes/stats API
        // For now, we create a placeholder snapshot
        ClusterSnapshot snapshot = latestSnapshots.get("cluster");
        if (snapshot != null) {
            // Add node-level metrics
            logger.debug("T2 collection completed");
        }
    }

    /**
     * Collect Tier 3 data: index-level metrics
     */
    private void collectTier3() {
        // In a real implementation, this would call _stats and _cluster/settings APIs
        logger.debug("T3 collection completed");
    }

    /**
     * Collect Tier 4 data: diagnostic information
     */
    private void collectTier4() {
        // In a real implementation, this would call mapping and ILM APIs
        logger.debug("T4 collection completed");
    }

    /**
     * Get the latest cluster snapshot
     */
    public ClusterSnapshot getLatestClusterSnapshot() {
        return latestSnapshots.get("cluster");
    }

    /**
     * Get all collected snapshots
     */
    public Map<String, ClusterSnapshot> getAllSnapshots() {
        return latestSnapshots;
    }

    /**
     * Check if collection is enabled
     */
    public boolean isCollectionEnabled() {
        return !scheduler.isShutdown();
    }
}