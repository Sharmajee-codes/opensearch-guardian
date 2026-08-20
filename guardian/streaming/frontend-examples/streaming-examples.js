/**
 * Example: Connecting to the Guardian Streaming API using Server-Sent Events (SSE)
 * This example shows how to consume real-time diagnostic findings from the backend.
 *
 * Backend endpoint: /api/stream/sse
 *
 * Usage in a React component:
 *   useEffect(() => {
 *     const eventSource = new EventSource('/api/stream/sse');
 *     eventSource.onmessage = (event) => {
 *       const data = JSON.parse(event.data);
 *       // Handle the streaming data (e.g., update state for charts)
 *       console.log('Received streaming data:', data);
 *     };
 *     return () => {
 *       eventSource.close();
 *     };
 *   }, []);
 *
 * Note: The backend sends messages with the following format:
 *   id: <microsecond-timestamp>
 *   event: <event-type>  // "snapshot", "event", "heartbeat"
 *   data: <JSON-string>
 *
 * For Doctor Rules integration, the event type is "event" and the data contains:
 *   {
 *     "type": "event",
 *     "connectionId": "diagnostic-engine",
 *     "timestamp": "ISO 8601 datetime",
 *     "payload": {
 *       "eventType": "incidentDetected" | "incidentCleared",
 *       "data": {
 *         "rule_id": "RULE-001",
 *         "rule_name": "Cluster health is red or yellow",
 *         "severity": "critical",
 *         "confidence": 0.98,
 *         "entity_type": "cluster",
 *         "entity_id": "test-cluster",
 *         "observed_value": "red",
 *         "threshold_or_expected": "green",
 *         "condition_description": "Cluster health is red; 5 unassigned shards, 0 failed tasks",
 *         "remediation_guidance": "Investigate unassigned shards via _cluster/allocation/explain.",
 *         "snapshot_id": "snap-abc123",
 *         "analyzed_at": "2026-08-20T10:30:00.000Z",
 *         "evidence": [
 *           {
 *             "source_api": "_cluster/health",
 *             "field_path": "status",
 *             "observed_value": "red",
 *             "timestamp": "2026-08-20T10:30:00.000Z"
 *           }
 *         ]
 *       }
 *     }
 *   }
 */
export const startSSEStreaming = (onMessage, onError) => {
  const eventSource = new EventSource('/api/stream/sse');

  eventSource.onopen = () => {
    console.log('SSE connection opened');
  };

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (err) {
      console.error('Failed to parse SSE message:', err);
      onError(err);
    }
  };

  eventSource.onerror = (err) => {
    console.error('SSE connection error:', err);
    onError(err);
    // Optionally, you can try to reconnect here
  };

  return () => {
    eventSource.close();
  };
};

/**
 * Example: Connecting to the Guardian Streaming API using WebSocket
 * This example shows how to consume real-time diagnostic findings from the backend via WebSocket.
 *
 * Backend endpoint: /api/stream/ws
 *
 * Usage:
 *   const ws = new WebSocket('ws://localhost:3000/api/stream/ws');
 *   ws.onmessage = (event) => {
 *     const data = JSON.parse(event.data);
 *     // Handle the streaming data
 *     console.log('Received WebSocket data:', data);
 *   };
 */
export const startWebSocketStreaming = (onMessage, onError) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//${window.location.host}/api/stream/ws`);

  ws.onopen = () => {
    console.log('WebSocket connection opened');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (err) {
      console.error('Failed to parse WebSocket message:', err);
      onError(err);
    }
  };

  ws.onerror = (err) => {
    console.error('WebSocket connection error:', err);
    onError(err);
  };

  ws.onclose = () => {
    console.log('WebSocket connection closed');
  };

  return () => {
    ws.close();
  };
};