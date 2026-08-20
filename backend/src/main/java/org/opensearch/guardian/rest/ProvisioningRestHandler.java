package org.opensearch.guardian.rest;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.opensearch.client.node.NodeClient;
import org.opensearch.common.xcontent.XContentFactory;
import org.opensearch.core.rest.RestStatus;
import org.opensearch.rest.BaseRestHandler;
import org.opensearch.rest.BytesRestResponse;
import org.opensearch.rest.RestRequest;
import org.opensearch.rest.RestResponse;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * REST handler for Guardian provisioning endpoints.
 * Exposes:
 *   GET    /_plugins/guardian/provisioning/plans
 *   POST   /_plugins/guardian/provisioning/plans
 *   POST   /_plugins/guardian/provisioning/plans/{planId}/preflight
 *   POST   /_plugins/guardian/provisioning/plans/{planId}/apply
 *   POST   /_plugins/guardian/provisioning/plans/{planId}/verify
 *   POST   /_plugins/guardian/provisioning/plans/{planId}/rollback
 *   GET    /_plugins/guardian/provisioning/plans/{planId}/status
 */
public class ProvisioningRestHandler extends BaseRestHandler {

    // In-memory store for provisioning plans (in production, this would use OpenSearch indices)
    private static final ConcurrentHashMap<String, Map<String, Object>> PLANS = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Map<String, Object>> AUDIT_LOGS = new ConcurrentHashMap<>();

    // Generate unique plan IDs
    private static int planCounter = 0;

    @Override
    public String getName() {
        return "provisioning_rest_handler";
    }

    @Override
    public List<org.opensearch.rest.RestHandler.Route> routes() {
        return Arrays.asList(
                new org.opensearch.rest.RestHandler.Route(
                        org.opensearch.rest.RestRequest.Method.GET,
                        "/_plugins/guardian/provisioning/plans"),
                new org.opensearch.rest.RestHandler.Route(
                        org.opensearch.rest.RestRequest.Method.POST,
                        "/_plugins/guardian/provisioning/plans"),
                new org.opensearch.rest.RestHandler.Route(
                        org.opensearch.rest.RestRequest.Method.POST,
                        "/_plugins/guardian/provisioning/plans/{planId}/preflight"),
                new org.opensearch.rest.RestHandler.Route(
                        org.opensearch.rest.RestRequest.Method.POST,
                        "/_plugins/guardian/provisioning/plans/{planId}/apply"),
                new org.opensearch.rest.RestHandler.Route(
                        org.opensearch.rest.RestRequest.Method.POST,
                        "/_plugins/guardian/provisioning/plans/{planId}/verify"),
                new org.opensearch.rest.RestHandler.Route(
                        org.opensearch.rest.RestRequest.Method.POST,
                        "/_plugins/guardian/provisioning/plans/{planId}/rollback"),
                new org.opensearch.rest.RestHandler.Route(
                        org.opensearch.rest.RestRequest.Method.GET,
                        "/_plugins/guardian/provisioning/plans/{planId}/status")
        );
    }

    @Override
    protected org.opensearch.rest.BaseRestHandler.RestChannelConsumer prepareRequest(
            RestRequest request, NodeClient client) throws IOException {
        String path = request.path();
        String[] parts = path.split("/");

        if (path.endsWith("/_plugins/guardian/provisioning/plans")) {
            if (request.method() == org.opensearch.rest.RestRequest.Method.GET) {
                return channel -> channel.sendResponse(listPlans());
            } else if (request.method() == org.opensearch.rest.RestRequest.Method.POST) {
                return channel -> channel.sendResponse(createPlan(request));
            }
        } else if (path.matches(".*provisioning/plans/[^/]+/preflight")) {
            String planId = extractPlanId(path);
            return channel -> channel.sendResponse(runPreflight(planId, request));
        } else if (path.matches(".*provisioning/plans/[^/]+/apply")) {
            String planId = extractPlanId(path);
            return channel -> channel.sendResponse(applyPlan(planId, request));
        } else if (path.matches(".*provisioning/plans/[^/]+/verify")) {
            String planId = extractPlanId(path);
            return channel -> channel.sendResponse(verifyPlan(planId, request));
        } else if (path.matches(".*provisioning/plans/[^/]+/rollback")) {
            String planId = extractPlanId(path);
            return channel -> channel.sendResponse(rollbackPlan(planId, request));
        } else if (path.matches(".*provisioning/plans/[^/]+/status")) {
            String planId = extractPlanId(path);
            return channel -> channel.sendResponse(getPlanStatus(planId));
        }

        return channel -> channel.sendResponse(
                new BytesRestResponse(org.opensearch.core.rest.RestStatus.BAD_REQUEST,
                        XContentFactory.jsonBuilder().startObject()
                                .field("error", "Unknown provisioning endpoint: " + path)
                                .endObject())
        );
    }

    // =========================
    // Endpoint Handlers
    // =========================

    private RestResponse listPlans() throws IOException {
        return new BytesRestResponse(org.opensearch.core.rest.RestStatus.OK,
                XContentFactory.jsonBuilder().startObject()
                        .field("total", PLANS.size())
                        .field("plans", PLANS.values())
                        .endObject());
    }

    private RestResponse createPlan(RestRequest request) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        @SuppressWarnings("unchecked")
        Map<String, Object> planData = mapper.readValue(request.content().utf8ToString(), Map.class);

        String planId = "plan-" + (++planCounter);
        String timestamp = System.currentTimeMillis() + "Z";

        Map<String, Object> plan = new ConcurrentHashMap<>();
        plan.put("id", planId);
        plan.put("name", planData.getOrDefault("name", "Untitled Plan"));
        plan.put("type", planData.getOrDefault("type", "docker"));
        plan.put("status", "created");
        plan.put("preflightStatus", "not_run");
        plan.put("createdAt", timestamp);
        plan.put("updatedAt", timestamp);
        plan.put("settings", planData);

        PLANS.put(planId, plan);

        // Add audit entry
        addAuditEntry(planId, "plan_created", "system", plan);

        return new BytesRestResponse(org.opensearch.core.rest.RestStatus.CREATED,
                XContentFactory.jsonBuilder().startObject()
                        .field("plan", plan)
                        .endObject());
    }

    private RestResponse runPreflight(String planId, RestRequest request) throws IOException {
        if (!PLANS.containsKey(planId)) {
            return new BytesRestResponse(org.opensearch.core.rest.RestStatus.NOT_FOUND,
                    XContentFactory.jsonBuilder().startObject()
                            .field("error", "Plan not found: " + planId)
                            .endObject());
        }

        Map<String, Object> plan = PLANS.get(planId);
        plan.put("preflightStatus", "running");
        plan.put("updatedAt", System.currentTimeMillis() + "Z");

        // Simulate preflight checks
        Map<String, Object> checks = new ConcurrentHashMap<>();
        checks.put("total", 18);
        checks.put("passed", 15);
        checks.put("warnings", 2);
        checks.put("failed", 0);
        checks.put("status", "passed");
        checks.put("timestamp", System.currentTimeMillis() + "Z");

        plan.put("preflightChecks", checks);
        plan.put("preflightStatus", "passed");

        addAuditEntry(planId, "preflight_completed", "system", checks);

        return new BytesRestResponse(org.opensearch.core.rest.RestStatus.OK,
                XContentFactory.jsonBuilder().startObject()
                        .field("planId", planId)
                        .field("preflightChecks", checks)
                        .field("canProceed", true)
                        .endObject());
    }

    private RestResponse applyPlan(String planId, RestRequest request) throws IOException {
        if (!PLANS.containsKey(planId)) {
            return new BytesRestResponse(org.opensearch.core.rest.RestStatus.NOT_FOUND,
                    XContentFactory.jsonBuilder().startObject()
                            .field("error", "Plan not found: " + planId)
                            .endObject());
        }

        Map<String, Object> plan = PLANS.get(planId);
        plan.put("status", "applying");
        plan.put("updatedAt", System.currentTimeMillis() + "Z");

        addAuditEntry(planId, "apply_started", "system", plan);

        // Return pending status
        return new BytesRestResponse(org.opensearch.core.rest.RestStatus.ACCEPTED,
                XContentFactory.jsonBuilder().startObject()
                        .field("planId", planId)
                        .field("status", "applying")
                        .field("message", "Provisioning plan is being applied. Poll /status for updates.")
                        .endObject());
    }

    private RestResponse verifyPlan(String planId, RestRequest request) throws IOException {
        if (!PLANS.containsKey(planId)) {
            return new BytesRestResponse(org.opensearch.core.rest.RestStatus.NOT_FOUND,
                    XContentFactory.jsonBuilder().startObject()
                            .field("error", "Plan not found: " + planId)
                            .endObject());
        }

        Map<String, Object> plan = PLANS.get(planId);
        plan.put("status", "verified");
        plan.put("updatedAt", System.currentTimeMillis() + "Z");

        // Simulate verification results
        Map<String, Object> verification = new ConcurrentHashMap<>();
        verification.put("total", 4);
        verification.put("passed", 4);
        verification.put("failed", 0);
        verification.put("status", "passed");
        verification.put("timestamp", System.currentTimeMillis() + "Z");

        plan.put("verification", verification);
        plan.put("status", "completed");

        addAuditEntry(planId, "verify_completed", "system", verification);

        return new BytesRestResponse(org.opensearch.core.rest.RestStatus.OK,
                XContentFactory.jsonBuilder().startObject()
                        .field("planId", planId)
                        .field("verification", verification)
                        .field("status", "completed")
                        .endObject());
    }

    private RestResponse rollbackPlan(String planId, RestRequest request) throws IOException {
        if (!PLANS.containsKey(planId)) {
            return new BytesRestResponse(org.opensearch.core.rest.RestStatus.NOT_FOUND,
                    XContentFactory.jsonBuilder().startObject()
                            .field("error", "Plan not found: " + planId)
                            .endObject());
        }

        Map<String, Object> plan = PLANS.get(planId);
        plan.put("status", "rolled_back");
        plan.put("updatedAt", System.currentTimeMillis() + "Z");

        addAuditEntry(planId, "rollback_completed", "system", plan);

        return new BytesRestResponse(org.opensearch.core.rest.RestStatus.OK,
                XContentFactory.jsonBuilder().startObject()
                        .field("planId", planId)
                        .field("status", "rolled_back")
                        .field("message", "Provisioning plan has been rolled back successfully.")
                        .endObject());
    }

    private RestResponse getPlanStatus(String planId) throws IOException {
        if (!PLANS.containsKey(planId)) {
            return new BytesRestResponse(org.opensearch.core.rest.RestStatus.NOT_FOUND,
                    XContentFactory.jsonBuilder().startObject()
                            .field("error", "Plan not found: " + planId)
                            .endObject());
        }

        Map<String, Object> plan = PLANS.get(planId);
        return new BytesRestResponse(org.opensearch.core.rest.RestStatus.OK,
                XContentFactory.jsonBuilder().startObject()
                        .field("plan", plan)
                        .endObject());
    }

    // =========================
    // Helpers
    // =========================

    private String extractPlanId(String path) {
        // path format: /_plugins/guardian/provisioning/plans/{planId}/xxx
        String[] parts = path.split("/");
        for (int i = 0; i < parts.length; i++) {
            if ("plans".equals(parts[i]) && i + 1 < parts.length) {
                return parts[i + 1];
            }
        }
        return null;
    }

    private void addAuditEntry(String planId, String action, String user, Object details) {
        Map<String, Object> entry = new ConcurrentHashMap<>();
        entry.put("id", "audit-" + System.currentTimeMillis());
        entry.put("timestamp", System.currentTimeMillis() + "Z");
        entry.put("action", action);
        entry.put("user", user);
        entry.put("details", details);
        entry.put("result", "success");

        AUDIT_LOGS.computeIfAbsent(planId, k -> new ConcurrentHashMap<>());
        AUDIT_LOGS.get(planId).put("audit-" + System.currentTimeMillis(), entry);
    }
}
