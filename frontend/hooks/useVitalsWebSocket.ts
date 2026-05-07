"use client";

import { useEffect, useState, useRef, useCallback } from "react";

export interface VitalsMessage {
  heart_rate?: number;
  blood_pressure_systolic?: number;
  blood_pressure_diastolic?: number;
  temperature?: number;
  oxygen_saturation?: number;
  respiratory_rate?: number;
}

export interface VitalsAnalysisResult {
  status: "success" | "error";
  vitals?: VitalsMessage;
  analysis?: any;
  timestamp?: string;
  message?: string;
}

const MAX_RECONNECT_DELAY_MS = 30_000;

export function useVitalsWebSocket(
  patientId: string | undefined,
  enabled: boolean = true
) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<VitalsAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const isMounted = useRef(false);

  const clearReconnectTimer = () => {
    if (reconnectTimeout.current !== null) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }
  };

  const closeSocket = () => {
    if (ws.current) {
      // Null handlers first so they don't fire during the close() call
      ws.current.onopen = null;
      ws.current.onmessage = null;
      ws.current.onerror = null;
      ws.current.onclose = null;
      ws.current.close();
      ws.current = null;
    }
  };

  const connect = useCallback(() => {
    if (!isMounted.current || !patientId) return;

    closeSocket();

    try {
      // Derive WebSocket URL from NEXT_PUBLIC_API_URL so it works in all envs.
      const apiBase =
        process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const wsBase = apiBase
        .replace(/^https:/, "wss:")
        .replace(/^http:/, "ws:");
      const url = `${wsBase}/api/v1/vitals/ws/${patientId}`;

      const socket = new WebSocket(url);
      ws.current = socket;

      socket.onopen = () => {
        if (!isMounted.current) return;
        reconnectAttempts.current = 0;
        setIsConnected(true);
        setError(null);
      };

      socket.onmessage = (event) => {
        if (!isMounted.current) return;
        try {
          const data: VitalsAnalysisResult = JSON.parse(event.data);
          setLastMessage(data);
          if (data.status === "error") {
            setError(data.message ?? "Unknown error");
          }
        } catch {
          setError("Failed to parse server message");
        }
      };

      socket.onerror = () => {
        if (!isMounted.current) return;
        setError("WebSocket connection error");
        setIsConnected(false);
      };

      socket.onclose = () => {
        if (!isMounted.current) return;
        setIsConnected(false);
        // Exponential backoff reconnect (1 s → 2 s → 4 s … capped at 30 s)
        const delay = Math.min(
          1_000 * 2 ** reconnectAttempts.current,
          MAX_RECONNECT_DELAY_MS,
        );
        reconnectAttempts.current += 1;
        reconnectTimeout.current = setTimeout(() => {
          if (isMounted.current) connect();
        }, delay);
      };
    } catch {
      setError("Failed to connect to WebSocket");
      setIsConnected(false);
    }
  }, [patientId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!enabled || !patientId) return;

    isMounted.current = true;
    reconnectAttempts.current = 0;
    connect();

    return () => {
      isMounted.current = false;
      clearReconnectTimer();
      closeSocket();
      setIsConnected(false);
    };
  }, [patientId, enabled, connect]);

  const sendVitals = (vitals: VitalsMessage) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(vitals));
    } else {
      setError("WebSocket not connected");
    }
  };

  return { isConnected, lastMessage, error, sendVitals };
}
