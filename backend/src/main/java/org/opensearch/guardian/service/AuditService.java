package org.opensearch.guardian.service;

import org.opensearch.cluster.service.ClusterService;
import org.opensearch.common.settings.Settings;
import org.opensearch.common.inject.Inject;
import org.opensearch.common.lifecycle.AbstractLifecycleComponent;
import org.opensearch.threadpool.ThreadPool;
import org.opensearch.common.logging.Loggers;

import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;

import org.apache.logging.log4j.Logger;

import java.io.IOException;

/**
 * Service for managing audit logging.
 */
public class AuditService extends AbstractLifecycleComponent {

    private static final Logger logger = Loggers.getLogger(AuditService.class);

    private final Settings settings;
    private final Map<String, Object> auditLog;

    @Inject
    public AuditService(Settings settings) {
        super();
        this.settings = settings;
        this.auditLog = new ConcurrentHashMap<>();
    }

    @Override
    protected void doStart() {
        logger.info("AuditService started");
    }

    @Override
    protected void doStop() {
        logger.info("AuditService stopped");
    }

    @Override
    protected void doClose() throws IOException {
        logger.info("AuditService closed");
    }

    public void logEvent(String eventType, String message, Object details) {
        logger.info("AUDIT [{}] {}: {}", eventType, message, details);
        auditLog.put(System.currentTimeMillis() + "", Map.of(
                "type", eventType,
                "message", message,
                "details", details
        ));
    }

    public Map<String, Object> getAuditLog() {
        return auditLog;
    }
}