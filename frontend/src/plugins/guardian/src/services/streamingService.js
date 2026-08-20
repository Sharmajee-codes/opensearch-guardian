export function startSSEStreaming(onMessage, onError) {
  if (typeof EventSource === 'undefined') {
    const noop = () => {};
    noop._instance = null;
    return noop;
  }
  
  const es = new EventSource('/api/stream/sse');
  es.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (err) {
      onError(err);
    }
  };
  es.onerror = (err) => {
    onError(err);
    es.close(); // Close stream on error
  };
  
  const cleanup = () => es.close();
  cleanup._instance = es;
  return cleanup;
}

export function startWebSocketStreaming(onMessage, onError) {
  if (typeof WebSocket === 'undefined') {
    const noop = () => {};
    noop._instance = null;
    return noop;
  }
  
  const ws = new WebSocket('ws://localhost/api/stream/ws');
  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (err) {
      onError(err);
    }
  };
  ws.onerror = (err) => onError(err);
  ws.onclose = (event) => onError(event);
  
  const cleanup = () => ws.close();
  cleanup._instance = ws;
  return cleanup;
}
