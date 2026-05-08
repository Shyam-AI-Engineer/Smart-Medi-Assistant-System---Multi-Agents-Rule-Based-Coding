# Error Boundaries Implementation

## Overview

Error boundaries in Next.js 14+ catch rendering errors in child components and display a fallback UI instead of crashing the entire page. This prevents patients from seeing blank screens when a component fails.

## Structure

### Error Boundary Files

```
frontend/
├── app/
│   ├── error.tsx                 # Root-level error boundary
│   ├── login/error.tsx           # Login page error boundary
│   ├── (app)/error.tsx           # Patient dashboard error boundary
│   ├── doctor/error.tsx          # Doctor portal error boundary
│   └── admin/error.tsx           # Admin panel error boundary
├── components/
│   └── error/
│       └── ErrorBoundaryFallback.tsx  # Reusable error UI component
```

### Component Structure

```
ErrorBoundaryFallback
├── Displays alert icon
├── Shows error title and description
├── Shows error details (dev mode only)
├── "Try Again" button (calls reset())
└── "Home" button (navigates to /)
```

## How It Works

### Next.js Error Boundaries

In Next.js 14, `error.tsx` is a special file that acts as an error boundary for its segment:

```tsx
// app/(app)/error.tsx
"use client";

export default function AppError({
  error,      // The thrown error
  reset,      // Function to retry rendering
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ErrorBoundaryFallback error={error} reset={reset} />;
}
```

**Key points:**
- Must be marked with `"use client"` for error handling
- Catches errors in all nested routes of the segment
- `reset()` attempts to re-render; if it fails again, error propagates up
- Root `app/error.tsx` catches any uncaught errors (last resort)

### Error Propagation Chain

```
Patient navigates to /chat
    ↓
Renders app/(app)/chat/page.tsx
    ↓
Component throws error
    ↓
Caught by app/(app)/error.tsx
    ↓
Shows ErrorBoundaryFallback with "Try Again" button
    ↓
User clicks "Try Again"
    ↓
Calls reset() to re-render the page
```

If `reset()` fails, the error propagates to the root `app/error.tsx`.

## Coverage

| Route | Error Boundary |
|-------|----------------|
| `/` (home) | `app/error.tsx` |
| `/login` | `app/login/error.tsx` |
| `/chat`, `/vitals`, `/dashboard`, etc. | `app/(app)/error.tsx` |
| `/doctor/*` | `app/doctor/error.tsx` |
| `/admin/*` | `app/admin/error.tsx` |

## Development vs Production

**Development mode:**
- Error details and stack trace shown
- Helps identify bugs quickly

**Production mode:**
- Generic error message shown
- Error details hidden from users
- Error ID (digest) shown for support tickets

```tsx
showDetails={process.env.NODE_ENV === "development"}
```

## Testing

Error boundaries should be tested by:

1. **Unit tests** - Test ErrorBoundaryFallback component
2. **Integration tests** - Test error.tsx files with Next.js
3. **Manual testing** - Throw an error in a page component:

```tsx
// Temporarily add to any page component
if (someCondition) {
  throw new Error("Test error");
}
```

Run tests:
```bash
npm test -- error-boundaries.test.tsx
```

## Future Enhancements

1. **Error tracking** - Send errors to Sentry/DataDog
2. **Custom error pages** - Different UIs for 404, 500, etc.
3. **Retry logic** - Automatic retry with exponential backoff
4. **Analytics** - Track which errors users encounter most
5. **User notifications** - Toast/notification on error recovery

## Example: Testing Error Boundaries

```bash
# Start dev server
npm run dev

# Open browser console and add this to any page:
# throw new Error("Test error boundary")

# Expected: See error fallback instead of blank page
```

## Architecture Benefits

- **User-friendly**: No more blank screens during errors
- **Medical safety**: Patient data access not interrupted by component errors
- **Debugging**: Error digests help track production issues
- **Resilience**: Segment-level boundaries prevent full app crashes
