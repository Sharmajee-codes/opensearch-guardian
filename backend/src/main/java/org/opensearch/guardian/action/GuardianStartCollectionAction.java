package org.opensearch.guardian.action;

import org.opensearch.action.ActionRequest;
import org.opensearch.action.ActionRequestValidationException;
import org.opensearch.action.ActionType;
import org.opensearch.core.action.ActionResponse;
import org.opensearch.core.common.io.stream.StreamInput;
import org.opensearch.core.common.io.stream.StreamOutput;
import org.opensearch.common.xcontent.XContentFactory;
import org.opensearch.core.xcontent.ToXContent;
import org.opensearch.core.xcontent.XContentBuilder;

import java.io.IOException;

/**
 * Action to start Guardian collection.
 */
public class GuardianStartCollectionAction extends ActionType<GuardianStartCollectionAction.Response> {

    public static final String NAME = "cluster:monitor/guardian/start_collection";
    public static final GuardianStartCollectionAction INSTANCE = new GuardianStartCollectionAction();

    private GuardianStartCollectionAction() {
        super(NAME, Response::new);
    }

    public static class Request extends ActionRequest {
        public Request() {}
        public Request(StreamInput in) throws IOException {
            super(in);
        }
        @Override
        public void writeTo(StreamOutput out) throws IOException {
            // No fields to write
        }
        @Override
        public ActionRequestValidationException validate() {
            return null; // No validation needed
        }
    }

    public static class Response extends ActionResponse implements ToXContent {
        private boolean started;
        private String message;
        private long timestamp;

        public Response() {
            super();
        }

        public Response(boolean started, String message) {
            super();
            this.started = started;
            this.message = message;
            this.timestamp = System.currentTimeMillis();
        }

        public Response(StreamInput in) throws IOException {
            super(in);
            this.started = in.readBoolean();
            this.message = in.readString();
            this.timestamp = in.readLong();
        }

        @Override
        public void writeTo(StreamOutput out) throws IOException {
            out.writeBoolean(started);
            out.writeString(message);
            out.writeLong(timestamp);
        }

        @Override
        public XContentBuilder toXContent(XContentBuilder builder, Params params) throws IOException {
            builder.startObject();
            builder.field("started", started);
            builder.field("message", message);
            builder.field("timestamp", timestamp);
            builder.endObject();
            return builder;
        }

        public boolean isStarted() { return started; }
        public String getMessage() { return message; }
        public long getTimestamp() { return timestamp; }
    }
}