"use client";

import { useEffect, useState, useRef } from "react";

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

export function useVitalsWebSocket(
  patientId: string | undefined,
  enabled: boolean = true
) {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<VitalsAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!enabled || !patientId) return;

    const connectWebSocket = () => {
      try {
        // Determine WebSocket URL (backend is on port 8000)
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//localhost:8000/api/v1/vitals/ws/${patientId}`;

        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
          setIsConnected(true);
          setError(null);
        };

        ws.current.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            setLastMessage(data);
            if (data.status === "error") {
              setError(data.message || "Unknown error");
            }
          } catch (e) {
            setError("Failed to parse server message");
          }
        };

        ws.current.onerror = (event) => {
          setError("WebSocket connection error");
          setIsConnected(false);
        };

        ws.current.onclose = () => {
          setIsConnected(false);
        };
      } catch (e) {
        setError("Failed to connect to WebSocket");
        setIsConnected(false);
      }
    };

    connectWebSocket();

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [patientId, enabled]);

  const sendVitals = (vitals: VitalsMessage) => {
    if (ws.current && isConnected) {
      ws.current.send(JSON.stringify(vitals));
    } else {
      setError("WebSocket not connected");
    }
  };

  return {
    isConnected,
    lastMessage,
    error,
    sendVitals,
  };
}
