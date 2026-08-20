package org.opensearch.guardian.rest;

import org.junit.jupiter.api.Test;
import org.mockito.Mockito;
import org.opensearch.client.node.NodeClient;
import org.opensearch.rest.RestRequest;
import org.opensearch.rest.RestStatus;
import org.opensearch.rest.action.RestToXContentListener;

import java.io.IOException;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for GuardianStatusRestHandler.
 */
public class GuardianStatusRestHandlerTest {

    @Test
    public void testHandlerExists() {
        GuardianStatusRestHandler handler = new GuardianStatusRestHandler();
        assertNotNull(handler);
    }

    @Test
    public void testHandlerName() {
        GuardianStatusRestHandler handler = new GuardianStatusRestHandler();
        assertEquals("guardian_status_handler", handler.getName());
    }

    @Test
    public void testGetRoutes() {
        GuardianStatusRestHandler handler = new GuardianStatusRestHandler();
        assertNotNull(handler.getRoutes());
        assertEquals(1, handler.getRoutes().size());
    }
}
