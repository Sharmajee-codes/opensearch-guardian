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
 * Unit tests for DiagnosisService with implemented runDiagnosis().
 */
public class DiagnosisServiceTest {

    @Mock
    private ClusterService clusterService;

    @InjectMocks
    private DiagnosisService diagnosisService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void testDiagnosisServiceCreation() {
        assertNotNull(diagnosisService);
    }

    @Test
    public void testRunDiagnosis() {
        assertDoesNotThrow(() -> diagnosisService.runDiagnosis());
    }

    @Test
    public void testGetLastResultsAfterDiagnosis() {
        diagnosisService.runDiagnosis();
        Map<String, Object> results = diagnosisService.getLastResults();
        assertNotNull(results);
        assertEquals("completed", results.get("status"));
        assertTrue(results.containsKey("timestamp"));
    }

    @Test
    public void testGetLastResultsBeforeDiagnosis() {
        Map<String, Object> results = diagnosisService.getLastResults();
        assertNotNull(results);
        assertTrue(results.isEmpty());
    }
}
