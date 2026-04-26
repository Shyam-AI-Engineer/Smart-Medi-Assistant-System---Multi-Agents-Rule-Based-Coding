# MediAssist — Frontend

Production-grade Next.js 14 frontend for the Smart Medi Assistant System.
Built to feel like a real SaaS product, not a tutorial.

---

## Stack

- **Next.js 14** (App Router) + **TypeScript** (strict)
- **Tailwind CSS** with a custom design-system layer
- **React Query** (`@tanstack/react-query`) for data fetching
- **Zustand** for client state (auth)
- **Recharts** for vitals visualization
- **Axios** for the API client (with auto-attached JWT)
- **lucide-react** for icons

---

## Getting started

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit NEXT_PUBLIC_API_URL if your backend isn't on localhost:8000
npm run dev
```

Open http://localhost:3000.

The backend must be running at the URL set in `NEXT_PUBLIC_API_URL`
(default `http://localhost:8000`). All requests are sent to `/api/v1/*`.

---

## Folder structure

```
frontend/
├─ app/
│  ├─ layout.tsx                # Root layout (fonts, providers)
│  ├─ page.tsx                  # Landing page
│  ├─ globals.css               # Design tokens + base layer
│  ├─ login/page.tsx            # Auth (login + register)
│  └─ (app)/                    # Authenticated route group
│     ├─ layout.tsx             # Sidebar shell + auth guard
│     ├─ dashboard/page.tsx     # Vitals overview + charts
│     ├─ vitals/page.tsx        # Record + analyze
│     └─ chat/page.tsx          # AI clinical chat
│
├─ components/
│  ├─ ui/                       # Button, Card, Input, Badge, Loader, Modal, Logo, EmptyState
│  ├─ layout/                   # Sidebar, MobileTopbar, PageHeader
│  ├─ chat/                     # MessageBubble, ChatInput
│  ├─ dashboard/                # MetricCard, VitalsChart
│  ├─ vitals/                   # VitalsForm, AnalysisResult
│  └─ providers/                # QueryProvider
│
├─ hooks/
│  ├─ useAuth.ts                # useAuth + useRequireAuth
│  ├─ useVitals.ts              # history, store, analyze, profile
│  └─ useChat.ts                # send chat message
│
├─ lib/
│  ├─ api.ts                    # Axios instance + typed endpoints
│  ├─ auth.ts                   # localStorage session helpers
│  ├─ format.ts                 # date/relative-time formatters
│  └─ cn.ts                     # className merge util
│
├─ stores/
│  └─ authStore.ts              # Zustand auth store
│
├─ tailwind.config.ts           # Custom tokens (colors, shadows, animations)
└─ next.config.mjs              # API rewrites
```

---

## Design system

All visual decisions flow from `tailwind.config.ts` + `app/globals.css`.

### Color tokens

- `bg / bg-subtle / bg-elevated` — surface hierarchy
- `ink / ink-muted / ink-subtle / ink-inverse` — text scale
- `border / border-strong` — dividers
- `brand-*` (50–900) — primary accent (calm medical blue)
- `success / warning / danger` — status semantics

### Typography

- **Font**: Inter (loaded via `next/font` for zero CLS)
- Tight tracking on headings (`-0.01em` to `-0.02em`)
- Body sits at 14–15px for high readability without feeling dense

### Surfaces

- `surface` utility class = white card, subtle border, soft shadow
- Two shadow tiers: `shadow-card` (default) and `shadow-elevated` (hover/modal)
- Border radius scale: `sm 6 / DEFAULT 10 / lg 14 / xl 18 / 2xl 22`

### Motion

- `animate-fade-in` — 180ms entrance for messages, modals
- `animate-pulse-soft` — typing indicator
- All transitions ≤ 200ms — never feels sluggish

### Why these choices

- **Whitespace over decoration** — medical UIs must feel calm, not busy.
- **One accent color** — brand blue carries focus; status colors stay rare.
- **Subtle depth** — borders + soft shadows beat heavy elevation for trust.
- **Consistent 4px rhythm** — every spacing value is a multiple of 4.

---

## Auth flow

1. User submits `/login` form → `POST /api/v1/auth/login`
2. JWT + refresh token saved to `localStorage` via `lib/auth.ts`
3. Zustand store (`stores/authStore.ts`) holds the user object in memory
4. Axios request interceptor in `lib/api.ts` attaches `Authorization: Bearer …`
5. Response interceptor catches `401` → clears session → redirects to `/login?next=…`
6. `(app)/layout.tsx` uses `useRequireAuth()` to guard every protected route

---

## API integration

Single source of truth: [`lib/api.ts`](lib/api.ts).

```ts
import { endpoints } from "@/lib/api";

// In a hook or component
const { data } = useQuery({
  queryKey: ["vitals-history", patientId],
  queryFn: () => endpoints.vitalsHistory(patientId, 30, 0),
  enabled: Boolean(patientId),
});
```

All endpoints are typed against the backend's Pydantic schemas
(`VitalsStoreResponse`, `VitalsAnalysis`, `ChatResponse`, etc.).

Errors go through `getApiErrorMessage()` which extracts FastAPI's
`detail` field and falls back gracefully.

---

## Pages

### `/` — Landing
Marketing hero, three feature cards, sign-in CTA.

### `/login` — Auth
Two-pane layout: form on the left, branded gradient panel on the right.
Toggles between login and register without a route change.

### `/dashboard` — Patient overview
- 4 metric cards (HR, BP, SpO₂, Temp) with trend badges
- 4 line charts with normal-range reference bands (Recharts)
- Recent readings table with anomaly flags
- Empty state when no vitals exist yet

### `/vitals` — Record + analyze
- Form with inline validation, range hints, and unit suffixes
- Submits to `POST /api/v1/vitals/` (stored + analyzed + trend)
- `AnalysisResult` card renders status badge, per-vital breakdown,
  recommendations, and escalation banner when triggered

### `/chat` — AI clinical chat
- Suggestion cards for empty state
- User/assistant message bubbles with avatars
- Auto-scroll, typing indicator, agent + source badges
- Disclaimer footer per response

---

## Reusable component contracts

| Component | Variants | Sizes | Notes |
|---|---|---|---|
| `Button` | primary, secondary, ghost, danger | sm, md, lg | `loading` prop, `fullWidth` prop |
| `Input` | text, number, email, password | — | `label`, `hint`, `error`, `prefix`, `suffix` |
| `Textarea` | — | — | Same field props as `Input` |
| `Card` | — | — | Composable: `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter` |
| `Badge` | tones: neutral, brand, success, warning, danger | — | Optional `dot` |
| `Loader` | — | sm, md, lg | `FullPageLoader`, `TypingDots` exported alongside |
| `Modal` | — | — | Esc-to-close, click-outside, backdrop blur |
| `EmptyState` | — | — | Icon + title + description + action |

---

## Scripts

```bash
npm run dev         # Start dev server on :3000
npm run build       # Production build
npm run start       # Start production server
npm run lint        # ESLint
npm run type-check  # tsc --noEmit
```

---

## Notes for backend pairing

- The auth response shape expected by the frontend matches
  `TokenResponse` in `lib/api.ts`. If backend returns different field
  names, update the typed wrappers there — components stay untouched.
- The chat endpoint is currently `POST /api/v1/chat` returning
  `{ response, agent_used, confidence_score, sources?, tokens_used? }`.
- `useMyPatientProfile()` calls `GET /api/v1/patients/me`. The vitals
  page degrades gracefully to stateless `/analyze` if no profile exists.
