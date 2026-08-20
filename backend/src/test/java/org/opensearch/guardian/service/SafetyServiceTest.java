package org.opensearch.guardian.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;

import java.util.HashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for SafetyService with implemented enforcePolicy().
 */
public class SafetyServiceTest {

    @Mock
    private SecurityService securityService;

    @InjectMocks
    private SafetyService safetyService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void testSafetyServiceCreation() {
        assertNotNull(safetyService);
    }

    @Test
    public void testEnforcePolicyWithValidPermission() {
        when(securityService.hasPermission("admin", "cluster:admin/provision")).thenReturn(true);
        
        Map<String, Object> context = new HashMap<>();
        context.put("user", "admin");
        context.put("action", "cluster:admin/provision");

        assertDoesNotThrow(() -> safetyService.enforcePolicy("test_policy", context));
    }

    @Test
    public void testEnforcePolicyWithoutPermission() {
        when(securityService.hasPermission("user", "cluster:admin/provision")).thenReturn(false);
        
        Map<String, Object> context = new HashMap<>();
        context.put("user", "user");
        context.put("action", "cluster:admin/provision");

        assertThrows(SecurityException.class, () -> {
            safetyService.enforcePolicy("test_policy", context);
        });
    }

    @Test
    public void testEnforcePolicyWithNullUser() {
        Map<String, Object> context = new HashMap<>();
        context.put("action", "cluster:monitor/health");

        // Should not throw, just log warning
        assertDoesNotThrow(() -> safetyService.enforcePolicy("test_policy", context));
    }

    @Test
    public void testEnforcePolicyWithNullAction() {
        Map<String, Object> context = new HashMap<>();
        context.put("user", "admin");

        // Should not throw, just log warning
        assertDoesNotThrow(() -> safetyService.enforcePolicy("test_policy", context));
    }

    @Test
    public void testGetSafetyConfigReturnsMap() {
        assertNotNull(safetyService.getSafetyConfig());
    }
}
