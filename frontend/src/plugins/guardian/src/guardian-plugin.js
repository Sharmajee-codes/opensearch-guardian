/**
 * OpenSearch Dashboards Guardian Plugin
 * Main plugin entry point for the Dashboards plugin
 */

import { schema } from '@kbn/config-schema';

export class GuardianPlugin {
    providerName = 'guardian';
    title = 'Guardian';
    theme = {
        darkMode: true
    };
    requiredDependencies = [];
    priority = 100;

    constructor(kibana) {
        this.kibana = kibana;
    }

    async init(kibana) {
        const { server, lifecycle, config, uiSettings, chrome, savedObjects } = kibana;

        // Register backend API proxy routes
        server.route({
            path: '/api/guardian/cluster/health',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/cluster/health');
            }
        });

        server.route({
            path: '/api/guardian/diagnosis/run',
            method: 'POST',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/diagnosis/run', 'POST');
            }
        });

        server.route({
            path: '/api/guardian/diagnosis/findings',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/diagnosis/findings');
            }
        });

        server.route({
            path: '/api/guardian/optimization/advice',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/optimization/advice');
            }
        });

        server.route({
            path: '/api/guardian/optimization/run',
            method: 'POST',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/optimization/run', 'POST');
            }
        });

        server.route({
            path: '/api/guardian/capacity/planning',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/capacity/planning');
            }
        });

        server.route({
            path: '/api/guardian/provisioning/preflight',
            method: 'POST',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/provisioning/preflight', 'POST');
            }
        });

        server.route({
            path: '/api/guardian/provisioning/approve',
            method: 'POST',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/provisioning/approve', 'POST');
            }
        });

        server.route({
            path: '/api/guardian/audit/log',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/audit/log');
            }
        });

        server.route({
            path: '/api/guardian/provisioning/plans',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/provisioning/plans');
            }
        });

        server.route({
            path: '/api/guardian/provisioning/plans',
            method: 'POST',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/provisioning/plans', 'POST');
            }
        });

        server.route({
            path: '/api/guardian/provisioning/preflight',
            method: 'POST',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/provisioning/preflight', 'POST');
            }
        });

        server.route({
            path: '/api/guardian/provisioning/apply',
            method: 'POST',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/provisioning/apply', 'POST');
            }
        });

        server.route({
            path: '/api/guardian/provisioning/verify',
            method: 'POST',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/provisioning/verify', 'POST');
            }
        });

        server.route({
            path: '/api/guardian/provisioning/rollback',
            method: 'POST',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/provisioning/rollback', 'POST');
            }
        });

        server.route({
            path: '/api/guardian/provisioning/status/{planId}',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, `/_plugins/guardian/provisioning/status/${request.params.planId}`);
            }
        });

        server.route({
            path: '/api/guardian/nodes/stats',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/nodes/stats');
            }
        });

        server.route({
            path: '/api/guardian/indices/stats',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/indices/stats');
            }
        });

        server.route({
            path: '/api/guardian/shards/stats',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/shards/stats');
            }
        });

        server.route({
            path: '/api/guardian/live/monitoring',
            method: 'GET',
            handler: async (request, h) => {
                return this.proxyToBackend(request, '/_plugins/guardian/live/monitoring');
            }
        });

        // Register UI on appLoaded
        lifecycle.on('appLoaded', () => {
            // Add to navigation
            if (chrome) {
                chrome.addToNavigation({
                    id: 'guardian',
                    title: 'Guardian',
                    url: '/app/guardian#/overview',
                    icon: 'guardianIcon',
                    order: 100
                });
            }

            // Register visualizations
            this.registerVisualizations(kibana);
        });

        return {};
    }

    async proxyToBackend(request, path, method = 'GET') {
        const { server } = this.kibana;
        // Use OpenSearch Dashboards server proxy to call backend plugin
        return server.inject({
            method,
            url: path,
            payload: request.payload,
            headers: {
                ...request.headers,
                'content-type': 'application/json'
            }
        });
    }

    registerVisualizations(kibana) {
        // Register custom visualizations here
        // Example: kibana.visualization.register(...)
    }
}
