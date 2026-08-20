package org.opensearch.guardian.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.opensearch.cluster.service.ClusterService;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for OptimizationService with implemented runOptimization().
 */
public class OptimizationServiceTest {

    @Mock
    private ClusterService clusterService;

    @InjectMocks
    private OptimizationService optimizationService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void testOptimizationServiceCreation() {
        assertNotNull(optimizationService);
    }

    @Test
    public void testRunOptimization() {
        assertDoesNotThrow(() -> optimizationService.runOptimization());
    }

    @Test
    public void testGetOptimizationResultsAfterOptimization() {
        optimizationService.runOptimization();
        Map<String, Object> results = optimizationService.getOptimizationResults();
        assertNotNull(results);
        assertEquals("completed", results.get("status"));
        assertTrue(results.containsKey("timestamp"));
    }

    @Test
    public void testGetOptimizationResultsBeforeOptimization() {
        Map<String, Object> results = optimizationService.getOptimizationResults();
        assertNotNull(results);
        assertTrue(results.isEmpty());
    }
}
