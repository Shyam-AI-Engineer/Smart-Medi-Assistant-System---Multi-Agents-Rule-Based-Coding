"use client";

import { useState, useRef, useCallback } from "react";

export type RecorderState = "idle" | "recording" | "error";

export interface UseVoiceRecorderReturn {
  state: RecorderState;
  transcript: string | null;
  error: string | null;
  startRecording: () => void;
  stopRecording: () => void;
  reset: () => void;
}

export function useVoiceRecorder(): UseVoiceRecorderReturn {
  const [state, setState] = useState<RecorderState>("idle");
  const [transcript, setTranscript] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recognitionRef = useRef<any>(null);
  const finalTextRef = useRef<string>("");

  const startRecording = useCallback(() => {
    setError(null);
    setTranscript(null);
    finalTextRef.current = "";

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const w = typeof window !== "undefined" ? (window as any) : null;
    const SpeechRecognitionAPI = w?.SpeechRecognition || w?.webkitSpeechRecognition;

    if (!SpeechRecognitionAPI) {
      setError("Speech recognition is not supported. Please use Chrome or Edge.");
      setState("error");
      return;
    }

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognition: any = new SpeechRecognitionAPI();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: { results: SpeechRecognitionResultList }) => {
      let final = "";
      for (let i = 0; i < event.results.length; i++) {
        if (event.results[i].isFinal) {
          final += event.results[i][0].transcript;
        }
      }
      if (final) finalTextRef.current = final;
    };

    recognition.onerror = (event: { error: string }) => {
      if (event.error === "not-allowed") {
        setError("Microphone access denied. Please allow microphone permission and try again.");
      } else if (event.error === "no-speech") {
        setError("No speech detected. Please try again.");
      } else if (event.error === "network") {
        setError("Network error during speech recognition. Please try again.");
      } else {
        setError("Speech recognition failed. Please try again.");
      }
      setState("error");
    };

    recognition.onend = () => {
      if (finalTextRef.current) {
        setTranscript(finalTextRef.current);
      }
      setState("idle");
    };

    try {
      recognition.start();
      recognitionRef.current = recognition;
      setState("recording");
    } catch {
      setError("Could not start speech recognition. Please try again.");
      setState("error");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.abort();
      recognitionRef.current = null;
    }
    setTranscript(null);
    setError(null);
    setState("idle");
    finalTextRef.current = "";
  }, []);

  return { state, transcript, error, startRecording, stopRecording, reset };
}
