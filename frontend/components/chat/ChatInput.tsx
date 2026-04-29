"use client";

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import { ArrowUp, Mic, MicOff } from "lucide-react";
import { cn } from "@/lib/cn";
import { useVoiceRecorder } from "@/hooks/useVoiceRecorder";

interface ChatInputProps {
  value: string;
  onChange: (v: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder = "Ask a medical question…",
}: ChatInputProps) {
  const ref = useRef<HTMLTextAreaElement>(null);
  const [voiceError, setVoiceError] = useState<string | null>(null);

  const { state: recorderState, transcript, error: recorderError, startRecording, stopRecording, reset } =
    useVoiceRecorder();

  // Auto-resize textarea
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 180) + "px";
  }, [value]);

  // Insert transcript into input when speech recognition finishes
  useEffect(() => {
    if (!transcript) return;
    onChange(value ? value + " " + transcript : transcript);
    reset();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [transcript]);

  // Show recorder errors
  useEffect(() => {
    if (recorderError) setVoiceError(recorderError);
  }, [recorderError]);

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) onSubmit();
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (value.trim() && !disabled) onSubmit();
  }

  function handleMicClick() {
    setVoiceError(null);
    if (recorderState === "recording") {
      stopRecording();
    } else {
      startRecording();
    }
  }

  const isRecording = recorderState === "recording";
  const canSend = value.trim().length > 0 && !disabled;

  return (
    <div className="space-y-1.5">
      <form
        onSubmit={handleSubmit}
        className={cn(
          "relative flex items-end gap-2 p-2 pr-2 rounded-xl bg-bg-elevated border border-border shadow-card",
          "focus-within:border-brand-500 focus-within:shadow-focus transition-shadow",
        )}
      >
        <textarea
          ref={ref}
          rows={1}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "flex-1 resize-none bg-transparent border-0 outline-none",
            "px-3 py-2.5 text-[15px] text-ink placeholder:text-ink-subtle",
            "max-h-[180px]",
          )}
        />

        {/* Mic button */}
        <button
          type="button"
          onClick={handleMicClick}
          disabled={disabled}
          aria-label={isRecording ? "Stop recording" : "Start voice input"}
          title={isRecording ? "Stop recording" : "Record voice message"}
          className={cn(
            "size-9 shrink-0 rounded-lg flex items-center justify-center transition-colors",
            isRecording
              ? "bg-red-500 text-white hover:bg-red-600 animate-pulse"
              : "bg-bg-subtle text-ink-muted hover:bg-bg-hover hover:text-ink",
            disabled && "cursor-not-allowed opacity-50",
          )}
        >
          {isRecording ? (
            <MicOff className="size-4" />
          ) : (
            <Mic className="size-4" />
          )}
        </button>

        {/* Send button */}
        <button
          type="submit"
          disabled={!canSend}
          aria-label="Send message"
          className={cn(
            "size-9 shrink-0 rounded-lg flex items-center justify-center transition-colors",
            canSend
              ? "bg-brand-600 text-white hover:bg-brand-700"
              : "bg-bg-subtle text-ink-subtle cursor-not-allowed",
          )}
        >
          <ArrowUp className="size-4" />
        </button>
      </form>

      {/* Voice status / error */}
      {isRecording && (
        <p className="text-xs text-red-600 px-1 flex items-center gap-1">
          <span className="inline-block size-2 rounded-full bg-red-500 animate-pulse" />
          Listening… click the mic again to stop
        </p>
      )}
      {voiceError && (
        <p className="text-xs text-danger-600 px-1">{voiceError}</p>
      )}
    </div>
  );
}
