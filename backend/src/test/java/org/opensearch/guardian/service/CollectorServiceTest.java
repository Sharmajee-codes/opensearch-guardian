package org.opensearch.guardian.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.opensearch.cluster.service.ClusterService;
import org.opensearch.common.settings.Settings;
import org.opensearch.threadpool.ThreadPool;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for CollectorService.
 */
public class CollectorServiceTest {

    @Mock
    private ClusterService clusterService;

    @Mock
    private ThreadPool threadPool;

    private Settings settings;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        settings = Settings.builder()
            .put("guardian.enabled", true)
            .put("guardian.collection.interval", "30s")
            .put("guardian.max.concurrent.collections", 10)
            .build();
    }

    @Test
    public void testCollectorServiceCreation() {
        CollectorService service = new CollectorService(clusterService, threadPool, settings);
        assertNotNull(service);
    }

    @Test
    public void testCollectorServiceIsNotNull() {
        CollectorService service = new CollectorService(clusterService, threadPool, settings);
        assertFalse(service.isCollectionEnabled() == false); // scheduler not shutdown initially
    }

    @Test
    public void testGetLatestClusterSnapshotReturnsNullInitially() {
        CollectorService service = new CollectorService(clusterService, threadPool, settings);
        assertNull(service.getLatestClusterSnapshot());
    }
}
