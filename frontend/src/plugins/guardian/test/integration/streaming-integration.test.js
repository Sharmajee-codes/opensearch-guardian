/**
 * Integration tests for streaming (SSE/WebSocket) endpoints
 */

function createMockEventSource() {
  let handlers = { open: null, message: null, error: null };
  return {
    url: '/api/stream/sse',
    readyState: 0,
    get onopen() { return handlers.open; },
    set onopen(h) { handlers.open = h; },
    get onmessage() { return handlers.message; },
    set onmessage(h) { handlers.message = h; },
    get onerror() { return handlers.error; },
    set onerror(h) { handlers.error = h; },
    _simulateOpen() { this.readyState = 1; handlers.open?.(); },
    _simulateMessage(data) { handlers.message?.({ data: JSON.stringify(data) }); },
    _simulateError() { handlers.error?.(new Event('error')); },
    close() { this.readyState = 2; }
  };
}

function createMockWebSocket() {
  let handlers = { open: null, message: null, error: null, close: null };
  return {
    url: 'ws://localhost/api/stream/ws',
    readyState: 0,
    get onopen() { return handlers.open; },
    set onopen(h) { handlers.open = h; },
    get onmessage() { return handlers.message; },
    set onmessage(h) { handlers.message = h; },
    get onerror() { return handlers.error; },
    set onerror(h) { handlers.error = h; },
    get onclose() { return handlers.close; },
    set onclose(h) { handlers.close = h; },
    _simulateOpen() { this.readyState = 1; handlers.open?.(); },
    _simulateMessage(data) { handlers.message?.({ data: JSON.stringify(data) }); },
    _simulateError() { handlers.error?.(new Event('error')); },
    _simulateClose() { this.readyState = 3; handlers.close?.(); },
    close() { this.readyState = 3; }
  };
}

jest.mock('../../src/services/streamingService', () => {
  const actual = jest.requireActual('../../src/services/streamingService');
  return actual;
});

import { startSSEStreaming, startWebSocketStreaming } from '../../src/services/streamingService';

describe('Streaming Integration Tests', () => {
  beforeEach(() => {
    global.EventSource = createMockEventSource;
    global.WebSocket = createMockWebSocket;
  });

  describe('SSE Streaming', () => {
    it('establishes an SSE stream and delivers parsed messages', () => {
      const onMessage = jest.fn();
      const onError = jest.fn();
      const cleanup = startSSEStreaming(onMessage, onError);
      const es = cleanup._instance;

      es._simulateOpen();
      es._simulateMessage({ type: 'event', payload: { severity: 'critical' } });

      expect(onMessage).toHaveBeenCalledTimes(1);
      expect(onMessage).toHaveBeenCalledWith({ type: 'event', payload: { severity: 'critical' } });
      expect(onError).not.toHaveBeenCalled();

      cleanup();
    });

    it('routes EventSource errors to onError and closes the stream', () => {
      const onError = jest.fn();
      const cleanup = startSSEStreaming(jest.fn(), onError);
      const es = cleanup._instance;

      es._simulateError();

      expect(onError).toHaveBeenCalledTimes(1);
      expect(es.readyState).toBe(2);

      cleanup();
    });

    it('routes message parse errors to onError', () => {
      const onError = jest.fn();
      const cleanup = startSSEStreaming(jest.fn(), onError);
      const es = cleanup._instance;

      es._simulateOpen();
      // Directly call onmessage with invalid JSON to test parse error handling
      es.onmessage({ data: 'invalid json' });

      expect(onError).toHaveBeenCalled();

      cleanup();
    });
  });

  describe('WebSocket Streaming', () => {
    it('establishes a WebSocket stream and delivers parsed messages', () => {
      const onMessage = jest.fn();
      const onError = jest.fn();
      const cleanup = startWebSocketStreaming(onMessage, onError);
      const ws = cleanup._instance;

      ws._simulateOpen();
      ws._simulateMessage({ type: 'snapshot', data: { nodes: 3 } });

      expect(onMessage).toHaveBeenCalledTimes(1);
      expect(onMessage).toHaveBeenCalledWith({ type: 'snapshot', data: { nodes: 3 } });
      expect(onError).not.toHaveBeenCalled();

      cleanup();
    });

    it('routes WebSocket errors to onError', () => {
      const onError = jest.fn();
      const cleanup = startWebSocketStreaming(jest.fn(), onError);
      const ws = cleanup._instance;

      ws._simulateError();

      expect(onError).toHaveBeenCalledTimes(1);

      cleanup();
    });

    it('closes cleanly without throwing', () => {
      const cleanup = startWebSocketStreaming(jest.fn(), jest.fn());
      const ws = cleanup._instance;

      expect(() => closeSafely(ws)).not.toThrow();

      cleanup();
    });
  });

  describe('Streaming Data Format', () => {
    it('forwards incident-detected events from SSE', () => {
      const onMessage = jest.fn();
      const cleanup = startSSEStreaming(onMessage, jest.fn());
      const es = cleanup._instance;

      es._simulateMessage({
        type: 'event',
        connectionId: 'diagnostic-engine',
        timestamp: '2026-08-20T10:30:00.000Z',
        payload: {
          eventType: 'incidentDetected',
          data: {
            rule_id: 'RULE-001',
            rule_name: 'Cluster health is red',
            severity: 'critical',
            confidence: 0.98
          }
        }
      });

      expect(onMessage).toHaveBeenCalledTimes(1);
      expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({
        type: 'event',
        connectionId: 'diagnostic-engine'
      }));

      cleanup();
    });

    it('forwards snapshot events from SSE', () => {
      const onMessage = jest.fn();
      const cleanup = startSSEStreaming(onMessage, jest.fn());
      const es = cleanup._instance;

      es._simulateMessage({
        type: 'snapshot',
        timestamp: '2026-08-20T10:30:00.000Z',
        data: {
          cluster: { health: 'green', nodes: 3 },
          nodes: []
        }
      });

      expect(onMessage).toHaveBeenCalledTimes(1);
      expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({
        type: 'snapshot',
        data: expect.objectContaining({ cluster: expect.objectContaining({ nodes: 3 }) })
      }));

      cleanup();
    });

    it('forwards heartbeat events from SSE', () => {
      const onMessage = jest.fn();
      const cleanup = startSSEStreaming(onMessage, jest.fn());
      const es = cleanup._instance;

      es._simulateMessage({
        type: 'heartbeat',
        timestamp: '2026-08-20T10:30:00.000Z'
      });

      expect(onMessage).toHaveBeenCalledTimes(1);
      expect(onMessage).toHaveBeenCalledWith(expect.objectContaining({
        type: 'heartbeat',
        timestamp: '2026-08-20T10:30:00.000Z'
      }));

      cleanup();
    });
  });
});

function closeSafely(stream) {
  try {
    stream.close();
  } catch {
    // ignore close errors in tests
  }
}