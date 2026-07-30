import { useEffect, useRef } from 'react';
export const useWebSocket = (url: string, onMessage: (ev: MessageEvent) => void) => {
  const ws = useRef<WebSocket | null>(null);
  useEffect(() => {
    ws.current = new WebSocket(url);
    ws.current.onmessage = onMessage;
    return () => { ws.current?.close(); };
  }, [url]);
};