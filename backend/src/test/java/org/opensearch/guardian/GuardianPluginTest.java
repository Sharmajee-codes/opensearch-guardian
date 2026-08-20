package org.opensearch.guardian;

import org.junit.jupiter.api.Test;
import org.opensearch.common.settings.Settings;
import org.opensearch.test.OpenSearchTestCase;

import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.notNullValue;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Unit tests for the GuardianPlugin.
 * Verifies plugin loading, settings, and actions.
 */
public class GuardianPluginTest extends OpenSearchTestCase {

    @Test
    public void testPluginLoadsCorrectly() {
        Settings settings = Settings.builder()
                .put("guardian.enabled", true)
                .put("guardian.collection.interval", "30s")
                .put("guardian.max.concurrent.collections", 5)
                .build();

        GuardianPlugin plugin = new GuardianPlugin(settings);

        // Verify plugin is not null
        assertThat(plugin, notNullValue());
        assertThat(plugin.getName(), equalTo("guardian"));
    }

    @Test
    public void testPluginSettings() {
        Settings settings = Settings.builder()
                .put("guardian.enabled", true)
                .put("guardian.collection.interval", "30s")
                .put("guardian.max.concurrent.collections", 5)
                .build();

        GuardianPlugin plugin = new GuardianPlugin(settings);

        // Verify settings are returned
        var settingsList = plugin.getSettings();
        assertThat(settingsList, notNullValue());
        assertEquals(3, settingsList.size());

        // Verify specific settings exist
        boolean hasEnabled = settingsList.stream()
                .anyMatch(s -> s.getKey().equals("guardian.enabled"));
        boolean hasInterval = settingsList.stream()
                .anyMatch(s -> s.getKey().equals("guardian.collection.interval"));
        boolean hasMaxConcurrent = settingsList.stream()
                .anyMatch(s -> s.getKey().equals("guardian.max.concurrent.collections"));

        assertTrue(hasEnabled, "Should have guardian.enabled setting");
        assertTrue(hasInterval, "Should have guardian.collection.interval setting");
        assertTrue(hasMaxConcurrent, "Should have guardian.max.concurrent.collections setting");
    }

    @Test
    public void testPluginActions() {
        Settings settings = Settings.builder().build();
        GuardianPlugin plugin = new GuardianPlugin(settings);

        // Verify actions are returned
        var actions = plugin.getActions();
        assertThat(actions, notNullValue());
        assertEquals(3, actions.size());

        // Verify known actions exist
        boolean hasStartCollection = actions.stream()
                .anyMatch(a -> a.getName().equals("cluster:monitor/guardian/start_collection"));
        boolean hasStopCollection = actions.stream()
                .anyMatch(a -> a.getName().equals("cluster:monitor/guardian/stop_collection"));
        boolean hasGetStatus = actions.stream()
                .anyMatch(a -> a.getName().equals("cluster:monitor/guardian/status"));

        assertTrue(hasStartCollection, "Should have start_collection action");
        assertTrue(hasStopCollection, "Should have stop_collection action");
        assertTrue(hasGetStatus, "Should have get_status action");
    }

    @Test
    public void testPluginDisabled() {
        Settings settings = Settings.builder()
                .put("guardian.enabled", false)
                .build();

        GuardianPlugin plugin = new GuardianPlugin(settings);

        // When disabled, getRestHandlers should return empty list
        var handlers = plugin.getRestHandlers(settings,
                null, null, null, null, null, null);
        assertEquals(0, handlers.size(), "Should return no handlers when plugin is disabled");
    }
}