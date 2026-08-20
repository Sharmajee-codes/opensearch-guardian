package org.opensearch.guardian.rest;

import org.opensearch.client.node.NodeClient;
import org.opensearch.core.rest.RestStatus;
import org.opensearch.rest.BaseRestHandler;
import org.opensearch.rest.BytesRestResponse;
import org.opensearch.rest.RestRequest;
import org.opensearch.rest.RestResponse;
import org.opensearch.common.xcontent.XContentFactory;
import org.opensearch.common.logging.Loggers;

import java.io.IOException;
import java.util.Collections;
import java.util.List;

import org.apache.logging.log4j.Logger;

/**
 * REST handler for Guardian plugin status endpoint.
 * Exposes: GET /_guardian/status
 */
public class GuardianStatusRestHandler extends BaseRestHandler {

    private static final Logger logger = Loggers.getLogger(GuardianStatusRestHandler.class);

    @Override
    public String getName() {
        return "guardian_status_handler";
    }

    @Override
    public List<org.opensearch.rest.RestHandler.Route> routes() {
        return Collections.singletonList(
                new org.opensearch.rest.RestHandler.Route(
                        org.opensearch.rest.RestRequest.Method.GET,
                        "/_guardian/status"
                )
        );
    }

    @Override
    protected org.opensearch.rest.BaseRestHandler.RestChannelConsumer prepareRequest(
            RestRequest request, NodeClient client) throws IOException {
        logger.debug("Handling status request");

        // In a real implementation, this would:
        // 1. Call GuardianGetStatusAction
        // 2. Return actual cluster status

        // For now, return a proper status response
        return channel -> channel.sendResponse(
                new BytesRestResponse(
                        org.opensearch.core.rest.RestStatus.OK,
                        XContentFactory.jsonBuilder()
                                .startObject()
                                .field("plugin", "guardian")
                                .field("version", "1.0.0")
                                .field("status", "running")
                                .field("cluster_name", "guardian-cluster")
                                .field("nodes", 1)
                                .field("collection_enabled", true)
                                .endObject())
        );
    }
}
