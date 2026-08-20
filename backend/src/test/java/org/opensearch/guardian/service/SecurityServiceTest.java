package org.opensearch.guardian.service;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.opensearch.cluster.service.ClusterService;
import org.opensearch.common.settings.Settings;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for SecurityService with implemented hasPermission().
 */
public class SecurityServiceTest {

    @Mock
    private ClusterService clusterService;

    @InjectMocks
    private SecurityService securityService;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
    }

    @Test
    public void testSecurityServiceCreation() {
        assertNotNull(securityService);
    }

    @Test
    public void testHasPermissionWithNullUser() {
        assertFalse(securityService.hasPermission(null, "cluster:monitor/health"));
    }

    @Test
    public void testHasPermissionWithNullAction() {
        assertFalse(securityService.hasPermission("admin", null));
    }

    @Test
    public void testHasPermissionForGuardianServiceUser() {
        assertTrue(securityService.hasPermission("guardian_service", "cluster:admin/provision"));
    }

    @Test
    public void testHasPermissionForMonitorActions() {
        assertTrue(securityService.hasPermission("admin", "cluster:monitor/health"));
        assertTrue(securityService.hasPermission("admin", "indices:monitor/stats"));
    }

    @Test
    public void testHasPermissionForAdminActionWithAdminUser() {
        assertTrue(securityService.hasPermission("admin", "cluster:admin/shrink"));
    }

    @Test
    public void testHasPermissionForAdminActionWithNonAdmin() {
        assertFalse(securityService.hasPermission("regular_user", "cluster:admin/shrink"));
    }

    @Test
    public void testGetSecurityConfigReturnsMap() {
        assertNotNull(securityService.getSecurityConfig());
    }
}
