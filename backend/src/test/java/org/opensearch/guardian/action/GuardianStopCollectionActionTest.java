package org.opensearch.guardian.action;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for GuardianStopCollectionAction.
 */
public class GuardianStopCollectionActionTest {

    @Test
    public void testActionInstanceExists() {
        assertNotNull(GuardianStopCollectionAction.INSTANCE);
    }

    @Test
    public void testActionName() {
        String name = GuardianStopCollectionAction.NAME;
        assertNotNull(name);
        assertTrue(name.contains("stop_collection"));
    }
}
