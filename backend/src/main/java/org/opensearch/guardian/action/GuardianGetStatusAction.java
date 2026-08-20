package org.opensearch.guardian.action;

import org.opensearch.action.ActionRequest;
import org.opensearch.action.ActionRequestValidationException;
import org.opensearch.action.ActionType;
import org.opensearch.core.action.ActionResponse;
import org.opensearch.core.common.io.stream.StreamInput;
import org.opensearch.core.common.io.stream.StreamOutput;
import org.opensearch.core.xcontent.ToXContent;
import org.opensearch.core.xcontent.XContentBuilder;

import java.io.IOException;

/**
 * Action to get Guardian plugin status.
 */
public class GuardianGetStatusAction extends ActionType<GuardianGetStatusAction.Response> {

    public static final String NAME = "cluster:monitor/guardian/status";
    public static final GuardianGetStatusAction INSTANCE = new GuardianGetStatusAction();

    private GuardianGetStatusAction() {
        super(NAME, Response::new);
    }

    public static class Request extends ActionRequest {
        public Request() {}
        public Request(StreamInput in) throws IOException {
            super(in);
        }
        @Override
        public void writeTo(StreamOutput out) throws IOException {
            super.writeTo(out);
        }
        @Override
        public ActionRequestValidationException validate() {
            return null; // No validation needed
        }
    }

    public static class Response extends ActionResponse implements ToXContent {
        private String plugin;
        private String version;
        private String clusterName;
        private int nodes;
        private boolean collectionEnabled;
        private long collectionIntervalSeconds;
        private long timestamp;

        public Response() {
            super();
        }

        public Response(StreamInput in) throws IOException {
            super(in);
            this.plugin = in.readString();
            this.version = in.readString();
            this.clusterName = in.readString();
            this.nodes = in.readInt();
            this.collectionEnabled = in.readBoolean();
            this.collectionIntervalSeconds = in.readLong();
            this.timestamp = in.readLong();
        }

        @Override
        public void writeTo(StreamOutput out) throws IOException {
            out.writeString(plugin);
            out.writeString(version);
            out.writeString(clusterName);
            out.writeInt(nodes);
            out.writeBoolean(collectionEnabled);
            out.writeLong(collectionIntervalSeconds);
            out.writeLong(timestamp);
        }

        @Override
        public XContentBuilder toXContent(XContentBuilder builder, Params params) throws IOException {
            builder.startObject();
            builder.field("plugin", plugin);
            builder.field("version", version);
            builder.field("cluster", clusterName);
            builder.field("nodes", nodes);
            builder.field("collection_enabled", collectionEnabled);
            builder.field("collection_interval_seconds", collectionIntervalSeconds);
            builder.field("timestamp", timestamp);
            builder.endObject();
            return builder;
        }

        // Getters and setters
        public String getPlugin() { return plugin; }
        public void setPlugin(String plugin) { this.plugin = plugin; }
        public String getVersion() { return version; }
        public void setVersion(String version) { this.version = version; }
        public String getClusterName() { return clusterName; }
        public void setClusterName(String clusterName) { this.clusterName = clusterName; }
        public int getNodes() { return nodes; }
        public void setNodes(int nodes) { this.nodes = nodes; }
        public boolean isCollectionEnabled() { return collectionEnabled; }
        public void setCollectionEnabled(boolean collectionEnabled) { this.collectionEnabled = collectionEnabled; }
        public long getCollectionIntervalSeconds() { return collectionIntervalSeconds; }
        public void setCollectionIntervalSeconds(long collectionIntervalSeconds) { this.collectionIntervalSeconds = collectionIntervalSeconds; }
        public long getTimestamp() { return timestamp; }
        public void setTimestamp(long timestamp) { this.timestamp = timestamp; }
    }
}