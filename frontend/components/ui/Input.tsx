"use client";

import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";
import { cn } from "@/lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
  prefix?: ReactNode;
  suffix?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, hint, error, prefix, suffix, id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="label block">
            {label}
          </label>
        )}
        <div
          className={cn(
            "flex items-center gap-2 h-10 px-3 rounded-lg",
            "bg-bg-elevated border border-border",
            "transition-shadow duration-150",
            "focus-within:border-brand-500 focus-within:shadow-focus",
            error && "border-danger-500 focus-within:border-danger-500 focus-within:shadow-[0_0_0_3px_rgba(239,68,68,0.18)]",
          )}
        >
          {prefix && <span className="text-ink-subtle shrink-0">{prefix}</span>}
          <input
            ref={ref}
            id={inputId}
            className={cn(
              "flex-1 min-w-0 bg-transparent text-sm text-ink placeholder:text-ink-subtle",
              "outline-none disabled:cursor-not-allowed disabled:text-ink-subtle",
              className,
            )}
            {...props}
          />
          {suffix && <span className="text-ink-subtle shrink-0">{suffix}</span>}
        </div>
        {error ? (
          <p className="text-xs text-danger-600">{error}</p>
        ) : hint ? (
          <p className="hint">{hint}</p>
        ) : null}
      </div>
    );
  },
);
Input.displayName = "Input";

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, hint, error, id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className="space-y-1.5">
        {label && (
          <label htmlFor={inputId} className="label block">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            "w-full px-3 py-2.5 rounded-lg bg-bg-elevated border border-border",
            "text-sm text-ink placeholder:text-ink-subtle resize-y min-h-[88px]",
            "outline-none transition-shadow duration-150",
            "focus:border-brand-500 focus:shadow-focus",
            error && "border-danger-500",
            className,
          )}
          {...props}
        />
        {error ? (
          <p className="text-xs text-danger-600">{error}</p>
        ) : hint ? (
          <p className="hint">{hint}</p>
        ) : null}
      </div>
    );
  },
);
Textarea.displayName = "Textarea";
