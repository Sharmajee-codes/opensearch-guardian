package org.opensearch.guardian.service;

import org.opensearch.cluster.service.ClusterService;
import org.opensearch.common.settings.Settings;
import org.opensearch.common.inject.Inject;
import org.opensearch.common.lifecycle.AbstractLifecycleComponent;
import org.opensearch.threadpool.ThreadPool;
import org.opensearch.common.logging.Loggers;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.apache.logging.log4j.Logger;

import java.io.IOException;

/**
 * Service for managing safety policies and RBAC enforcement.
 */
public class SafetyService extends AbstractLifecycleComponent {

    private static final Logger logger = Loggers.getLogger(SafetyService.class);

    private final Settings settings;
    private final Map<String, Object> safetyConfig;
    private final SecurityService securityService;

    @Inject
    public SafetyService(Settings settings, SecurityService securityService) {
        super();
        this.settings = settings;
        this.securityService = securityService;
        this.safetyConfig = new ConcurrentHashMap<>();
    }

    @Override
    protected void doStart() {
        logger.info("SafetyService started");
    }

    @Override
    protected void doStop() {
        logger.info("SafetyService stopped");
    }

    @Override
    protected void doClose() throws IOException {
        logger.info("SafetyService closed");
    }

    /**
     * Enforce safety policy for given context.
     * Integrates with RBAC from SecurityService.
     */
    public void enforcePolicy(String policyName, Map<String, Object> context) {
        logger.info("Enforcing safety policy: {}", policyName);
        
        // Get user from context
        String user = (String) context.get("user");
        if (user == null) {
            logger.warn("No user in context for policy enforcement");
            return;
        }
        
        // Get action from context
        String action = (String) context.get("action");
        if (action == null) {
            logger.warn("No action in context for policy enforcement");
            return;
        }
        
        // Check permission via SecurityService
        if (!securityService.hasPermission(user, action)) {
            logger.warn("Permission denied for user {} to perform {}", user, action);
            throw new SecurityException(
                "User " + user + " does not have permission to perform " + action
            );
        }
        
        // Apply safety policy constraints
        logger.info("Safety policy {} enforced successfully for user {}", policyName, user);
    }

    public Map<String, Object> getSafetyConfig() {
        return safetyConfig;
    }
}
