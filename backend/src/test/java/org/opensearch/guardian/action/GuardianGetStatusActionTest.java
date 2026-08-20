package org.opensearch.guardian.action;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for GuardianGetStatusAction.
 */
public class GuardianGetStatusActionTest {

    @Test
    public void testActionInstanceExists() {
        assertNotNull(GuardianGetStatusAction.INSTANCE);
    }

    @Test
    public void testActionName() {
        assertEquals("cluster:monitor/guardian/status", GuardianGetStatusAction.NAME);
    }

    @Test
    public void testResponseCreation() {
        GuardianGetStatusAction.Response response = new GuardianGetStatusAction.Response();
        response.setPlugin("guardian");
        response.setVersion("1.0.0");
        response.setClusterName("test-cluster");
        response.setNodes(3);
        response.setCollectionEnabled(true);
        response.setCollectionIntervalSeconds(30);
        response.setTimestamp(System.currentTimeMillis());

        assertEquals("guardian", response.getPlugin());
        assertEquals("1.0.0", response.getVersion());
        assertEquals("test-cluster", response.getClusterName());
        assertEquals(3, response.getNodes());
        assertTrue(response.isCollectionEnabled());
        assertEquals(30, response.getCollectionIntervalSeconds());
    }
}
