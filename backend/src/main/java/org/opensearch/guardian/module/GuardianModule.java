package org.opensearch.guardian.module;

import org.opensearch.cluster.service.ClusterService;
import org.opensearch.common.inject.AbstractModule;
import org.opensearch.common.inject.Singleton;
import org.opensearch.common.settings.Settings;
import org.opensearch.guardian.service.AuditService;
import org.opensearch.guardian.service.CollectorService;
import org.opensearch.guardian.service.DiagnosisService;
import org.opensearch.guardian.service.OptimizationService;
import org.opensearch.guardian.service.ProvisioningService;
import org.opensearch.guardian.service.SafetyService;
import org.opensearch.guardian.service.SecurityService;
import org.opensearch.threadpool.ThreadPool;

/**
 * Guice module for binding Guardian plugin services.
 */
public class GuardianModule extends AbstractModule {

    @Override
    protected void configure() {
        // Bind services as singletons using proper Guice bindings
        bind(CollectorService.class).in(Singleton.class);
        bind(DiagnosisService.class).in(Singleton.class);
        bind(OptimizationService.class).in(Singleton.class);
        bind(ProvisioningService.class).in(Singleton.class);
        bind(SafetyService.class).in(Singleton.class);
        bind(SecurityService.class).in(Singleton.class);
        bind(AuditService.class).in(Singleton.class);

        // Note: Services are instantiated via @Inject constructors,
        // so Guice will automatically resolve dependencies
    }
}
