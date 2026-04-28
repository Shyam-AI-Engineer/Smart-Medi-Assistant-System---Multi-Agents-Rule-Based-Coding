import axios, { AxiosError, type AxiosInstance } from "axios";
import { auth } from "./auth";

const baseURL =
  (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = auth.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      auth.clear();
      const path = window.location.pathname;
      if (!path.startsWith("/login")) {
        window.location.href = `/login?next=${encodeURIComponent(path)}`;
      }
    }
    return Promise.reject(error);
  },
);

export function getApiErrorMessage(err: unknown, fallback = "Something went wrong"): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
    return err.message || fallback;
  }
  if (err instanceof Error) return err.message;
  return fallback;
}

// ──────────────────────────────────────────────────────────────────────
// Typed endpoint wrappers
// ──────────────────────────────────────────────────────────────────────

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  user_id: string;
  email: string;
  role: "patient" | "doctor" | "nurse" | "admin";
  full_name?: string;
}

export interface VitalRecord {
  id: string;
  patient_id?: string;
  heart_rate?: number | null;
  blood_pressure_systolic?: number | null;
  blood_pressure_diastolic?: number | null;
  temperature?: number | null;
  oxygen_saturation?: number | null;
  respiratory_rate?: number | null;
  weight?: number | null;
  notes?: string | null;
  anomaly_detected?: boolean;
  anomaly_score?: number | null;
  created_at: string;
}

export interface VitalAnalysisItem {
  vital_type: string;
  value: number;
  unit: string;
  status: string;
  severity: string;
  normal_range: Record<string, number>;
  explanation: string;
  recommendation: string;
  confidence: number;
}

export interface VitalsAnalysis {
  overall_status: "NORMAL" | "MODERATE" | "HIGH" | "CRITICAL" | string;
  severity_level: number;
  vital_analyses: VitalAnalysisItem[];
  critical_findings: string[];
  overall_assessment: string;
  recommendations: string[];
  should_escalate_to_triage: boolean;
  confidence_score: number;
  agent_used: string;
  tokens_used: number;
  timestamp: string;
  disclaimer: string;
  response: string;
  error?: boolean;
}

export interface VitalsStoreResponse {
  record: VitalRecord;
  analysis: VitalsAnalysis;
  trend: "WORSENING" | "IMPROVING" | "STABLE";
}

export interface VitalsHistoryResponse {
  patient_id: string;
  items: VitalRecord[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
}

export interface ChatMessage {
  id?: string;
  user_message: string;
  ai_response: string;
  agent_used?: string;
  confidence_score?: number;
  created_at?: string;
}

export interface SendChatPayload {
  message: string;
  patient_id?: string;
}

export interface ChatResponse {
  response: string;
  agent_used: string;
  confidence_score: number;
  sources?: { file: string; relevance?: string; source_type?: string; preview?: string }[];
  tokens_used?: number;
  context_documents_used?: number;
  timestamp?: string;
  error?: boolean;
}

export interface ChatHistoryResponse {
  items: ChatMessage[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
}

export interface PatientProfile {
  id: string;
  user_id: string;
  full_name?: string | null;
  date_of_birth?: string | null;
  medical_history?: string | null;
  allergies?: string | null;
  current_medications?: string | null;
  emergency_contact?: string | null;
}

export type VitalStatus = "NORMAL" | "MODERATE" | "HIGH" | "CRITICAL" | "UNKNOWN";
export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL" | "UNKNOWN";

export interface DoctorPatientSummary {
  id: string;
  user_id: string;
  full_name: string;
  age: number | null;
  date_of_birth: string | null;
  latest_vital_status: VitalStatus;
  risk_level: RiskLevel;
  latest_vital_timestamp: string | null;
  latest_vital_id: string | null;
}

export interface DoctorPatientsResponse {
  items: DoctorPatientSummary[];
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
}

export interface PatientDetailUser {
  user_id: string;
  email: string;
  full_name: string;
}

export interface PatientDetailPatient extends PatientProfile {
  full_name?: string;
  user?: PatientDetailUser;
}

export interface DoctorChatItem {
  id: string;
  user_message: string;
  ai_response: string;
  agent_used: string;
  confidence_score: number;
  created_at: string;
}

export interface PatientDetailSummary {
  latest_status: VitalStatus;
  risk_level: RiskLevel;
  total_messages: number;
  latest_vital_at: string | null;
}

export interface PatientDetailResponse {
  patient: PatientDetailPatient;
  vitals: VitalRecord[];
  chat_history: DoctorChatItem[];
  summary: PatientDetailSummary;
}

export const endpoints = {
  // Auth
  login: (payload: LoginPayload) =>
    api.post<TokenResponse>("/auth/login", payload).then((r) => r.data),
  register: (payload: RegisterPayload) =>
    api.post<TokenResponse>("/auth/register", payload).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),

  // Patient
  myProfile: () => api.get<PatientProfile>("/patients/me").then((r) => r.data),
  updateProfile: (payload: Partial<PatientProfile>) =>
    api.put<PatientProfile>("/patients/me", payload).then((r) => r.data),

  // Vitals
  storeVitals: (payload: Partial<VitalRecord> & { patient_id: string }) =>
    api.post<VitalsStoreResponse>("/vitals/", payload).then((r) => r.data),
  analyzeVitals: (payload: Partial<VitalRecord>) =>
    api.post<VitalsAnalysis>("/vitals/analyze", payload).then((r) => r.data),
  vitalsHistory: (patientId: string, limit = 20, offset = 0) =>
    api
      .get<VitalsHistoryResponse>(`/vitals/${patientId}`, { params: { limit, offset } })
      .then((r) => r.data),

  // Chat
  sendChat: (payload: SendChatPayload) =>
    api.post<ChatResponse>("/chat", payload).then((r) => r.data),
  chatHistory: (patientId: string, limit = 50, offset = 0) =>
    api.get<ChatHistoryResponse>(`/chat/history`, { params: { patient_id: patientId, limit, offset } }).then((r) => r.data),

  // Doctor Dashboard
  doctorPatients: (limit = 20, offset = 0) =>
    api
      .get<DoctorPatientsResponse>("/doctor/patients", { params: { limit, offset } })
      .then((r) => r.data),
  patientDetail: (patientId: string, vitalsLimit = 30, chatLimit = 20) =>
    api
      .get<PatientDetailResponse>(`/doctor/patients/${patientId}`, {
        params: { vitals_limit: vitalsLimit, chat_limit: chatLimit },
      })
      .then((r) => r.data),
};
