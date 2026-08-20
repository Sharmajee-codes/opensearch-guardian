package org.opensearch.guardian;

import org.junit.jupiter.api.Test;
import org.opensearch.common.settings.Settings;
import org.opensearch.test.OpenSearchIntegTestCase;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration test for GuardianPlugin with OpenSearch cluster.
 */
public class GuardianPluginIntegTest extends OpenSearchIntegTestCase {

    @Test
    public void testPluginLoads() {
        Settings settings = Settings.builder()
            .put("guardian.enabled", true)
            .put("guardian.collection.interval", "30s")
            .put("guardian.max.concurrent.collections", 10)
            .build();

        GuardianPlugin plugin = new GuardianPlugin(settings);
        assertNotNull(plugin);
        assertEquals("guardian", plugin.getName());
    }

    @Test
    public void testPluginActions() {
        Settings settings = Settings.EMPTY;
        GuardianPlugin plugin = new GuardianPlugin(settings);

        var actions = plugin.getActions();
        assertNotNull(actions);
        assertEquals(3, actions.size());

        boolean hasStart = actions.stream()
            .anyMatch(a -> a.getName().contains("start_collection"));
        boolean hasStop = actions.stream()
            .anyMatch(a -> a.getName().contains("stop_collection"));
        boolean hasStatus = actions.stream()
            .anyMatch(a -> a.getName().contains("status"));

        assertTrue(hasStart, "Should have start_collection action");
        assertTrue(hasStop, "Should have stop_collection action");
        assertTrue(hasStatus, "Should have status action");
    }
}
