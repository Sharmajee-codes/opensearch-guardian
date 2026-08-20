package org.opensearch.guardian.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.MockitoAnnotations;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for AuditService.
 */
public class AuditServiceTest {

    @InjectMocks
    private AuditService auditService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void testAuditServiceCreation() {
        assertNotNull(auditService);
    }

    @Test
    public void testLogEvent() {
        assertDoesNotThrow(() -> auditService.logEvent("TEST", "Test message", "Test details"));
    }

    @Test
    public void testGetAuditLogAfterLogging() {
        auditService.logEvent("CREATE", "Created resource", "id=123");
        Map<String, Object> log = auditService.getAuditLog();
        assertNotNull(log);
        assertFalse(log.isEmpty());
    }

    @Test
    public void testGetAuditLogBeforeLogging() {
        Map<String, Object> log = auditService.getAuditLog();
        assertNotNull(log);
        assertTrue(log.isEmpty());
    }

    @Test
    public void testLogMultipleEvents() {
        auditService.logEvent("CREATE", "Event 1", "data1");
        auditService.logEvent("UPDATE", "Event 2", "data2");
        auditService.logEvent("DELETE", "Event 3", "data3");

        Map<String, Object> log = auditService.getAuditLog();
        assertEquals(3, log.size());
    }
}
