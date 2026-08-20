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
 * Action to stop Guardian collection.
 */
public class GuardianStopCollectionAction extends ActionType<GuardianStopCollectionAction.Response> {

    public static final String NAME = "cluster:monitor/guardian/stop_collection";
    public static final GuardianStopCollectionAction INSTANCE = new GuardianStopCollectionAction();

    private GuardianStopCollectionAction() {
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
        private boolean stopped;
        private String message;
        private long timestamp;

        public Response() {
            super();
        }

        public Response(boolean stopped, String message) {
            super();
            this.stopped = stopped;
            this.message = message;
            this.timestamp = System.currentTimeMillis();
        }

        public Response(StreamInput in) throws IOException {
            super(in);
            this.stopped = in.readBoolean();
            this.message = in.readString();
            this.timestamp = in.readLong();
        }

        @Override
        public void writeTo(StreamOutput out) throws IOException {
            out.writeBoolean(stopped);
            out.writeString(message);
            out.writeLong(timestamp);
        }

        @Override
        public XContentBuilder toXContent(XContentBuilder builder, Params params) throws IOException {
            builder.startObject();
            builder.field("stopped", stopped);
            builder.field("message", message);
            builder.field("timestamp", timestamp);
            builder.endObject();
            return builder;
        }

        public boolean isStopped() { return stopped; }
        public String getMessage() { return message; }
        public long getTimestamp() { return timestamp; }
    }
}