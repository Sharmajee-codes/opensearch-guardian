package org.opensearch.guardian.service;

import org.opensearch.cluster.service.ClusterService;
import org.opensearch.common.settings.Settings;
import org.opensearch.common.inject.Inject;
import org.opensearch.common.lifecycle.AbstractLifecycleComponent;
import org.opensearch.threadpool.ThreadPool;
import org.opensearch.guardian.model.ClusterSnapshot;
import org.opensearch.common.logging.Loggers;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.apache.logging.log4j.Logger;

import java.io.IOException;

/**
 * Service that manages Guardian-specific collection tasks.
 * This is the main orchestrator for all data collection activities.
 */
public class GuardianCollectionService extends AbstractLifecycleComponent {

    private static final Logger logger = Loggers.getLogger(GuardianCollectionService.class);

    private final ClusterService clusterService;
    private final ThreadPool threadPool;
    private final Settings settings;
    private final CollectorService collectorService;
    private final Map<String, Object> collectionStatus;
    private final ScheduledExecutorService scheduler;

    @Inject
    public GuardianCollectionService(ClusterService clusterService, ThreadPool threadPool,
                                     Settings settings, CollectorService collectorService) {
        super();
        this.clusterService = clusterService;
        this.threadPool = threadPool;
        this.settings = settings;
        this.collectorService = collectorService;
        this.collectionStatus = new ConcurrentHashMap<>();
        this.scheduler = Executors.newScheduledThreadPool(2);
    }

    @Override
    protected void doStart() {
        logger.info("Starting GuardianCollectionService");
        startMonitoring();
    }

    @Override
    protected void doStop() {
        logger.info("Stopping GuardianCollectionService");
        scheduler.shutdown();
    }

    @Override
    protected void doClose() throws IOException {
        logger.info("GuardianCollectionService closed");
        scheduler.shutdownNow();
    }

    private void startMonitoring() {
        // Monitor collection health and log status
        scheduler.scheduleAtFixedRate(() -> {
            try {
                ClusterSnapshot snapshot = collectorService.getLatestClusterSnapshot();
                if (snapshot != null) {
                    collectionStatus.put("last_snapshot_time", snapshot.getCollectedAt().toString());
                    collectionStatus.put("cluster_health", snapshot.getHealthStatus());
                    collectionStatus.put("total_nodes", snapshot.getTotalNodes());
                    logger.debug("Collection status: health={}, nodes={}",
                            snapshot.getHealthStatus(), snapshot.getTotalNodes());
                }
            } catch (Exception e) {
                logger.error("Error collecting collection status: {}", e.getMessage());
            }
        }, 0, 30, TimeUnit.SECONDS);
    }

    /**
     * Get the current collection status
     */
    public Map<String, Object> getCollectionStatus() {
        Map<String, Object> status = new ConcurrentHashMap<>(collectionStatus);
        status.put("enabled", !scheduler.isShutdown());
        status.put("plugin_enabled", isPluginEnabled());
        return status;
    }

    /**
     * Check if the plugin is enabled via settings
     */
    public boolean isPluginEnabled() {
        return settings.getAsBoolean("guardian.enabled", true);
    }

    /**
     * Get the latest snapshot from the collector
     */
    public ClusterSnapshot getLatestSnapshot() {
        return collectorService.getLatestClusterSnapshot();
    }
}