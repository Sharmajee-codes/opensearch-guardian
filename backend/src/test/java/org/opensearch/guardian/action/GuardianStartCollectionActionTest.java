package org.opensearch.guardian.action;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for GuardianStartCollectionAction.
 */
public class GuardianStartCollectionActionTest {

    @Test
    public void testActionInstanceExists() {
        assertNotNull(GuardianStartCollectionAction.INSTANCE);
    }

    @Test
    public void testActionName() {
        String name = GuardianStartCollectionAction.NAME;
        assertNotNull(name);
        assertTrue(name.contains("start_collection"));
    }
}
