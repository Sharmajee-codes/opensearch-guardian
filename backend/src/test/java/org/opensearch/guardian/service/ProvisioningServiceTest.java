package org.opensearch.guardian.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.opensearch.cluster.service.ClusterService;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for ProvisioningService.
 */
public class ProvisioningServiceTest {

    @Mock
    private ClusterService clusterService;

    @InjectMocks
    private ProvisioningService provisioningService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void testProvisioningServiceCreation() {
        assertNotNull(provisioningService);
    }

    @Test
    public void testCreateProvisioningPlan() {
        Map<String, Object> plan = new HashMap<>();
        plan.put("index", "test-index");
        plan.put("shards", 3);

        assertDoesNotThrow(() -> provisioningService.createProvisioningPlan("plan-1", plan));
        assertNotNull(provisioningService.getProvisioningPlans());
    }

    @Test
    public void testGetProvisioningPlans() {
        Map<String, Object> plans = provisioningService.getProvisioningPlans();
        assertNotNull(plans);
        assertTrue(plans.isEmpty());
    }

    @Test
    public void testCreateMultiplePlans() {
        Map<String, Object> plan1 = new HashMap<>();
        plan1.put("index", "index-1");
        
        Map<String, Object> plan2 = new HashMap<>();
        plan2.put("index", "index-2");

        provisioningService.createProvisioningPlan("plan-1", plan1);
        provisioningService.createProvisioningPlan("plan-2", plan2);

        Map<String, Object> plans = provisioningService.getProvisioningPlans();
        assertEquals(2, plans.size());
    }
}
