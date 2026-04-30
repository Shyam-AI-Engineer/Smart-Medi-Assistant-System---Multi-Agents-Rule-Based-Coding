import axios, { AxiosError, type AxiosInstance } from "axios";
import { auth } from "./auth";

const baseURL =
  (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") + "/api/v1";

export const api: AxiosInstance = axios.create({
  baseURL,
  timeout: 30_000,
});

api.interceptors.request.use((config) => {
  const token = auth.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  // Only set Content-Type for non-FormData requests
  // FormData needs multipart/form-data, which axios sets automatically
  if (!(config.data instanceof FormData) && !config.headers["Content-Type"]) {
    config.headers["Content-Type"] = "application/json";
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
  feedback?: "thumbs_up" | "thumbs_down" | null;
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

export interface ChatStreamMeta {
  agent_used: string;
  confidence_score: number;
  sources?: ChatResponse["sources"];
  context_documents_used?: number;
}

export async function sendChatStream(
  payload: SendChatPayload,
  onToken: (token: string) => void,
  onDone: (meta: ChatStreamMeta) => void,
  onError: (msg: string) => void,
): Promise<void> {
  const streamURL =
    (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") +
    "/api/v1/chat/stream";

  const { auth: authLib } = await import("./auth");
  const token = authLib.getToken();

  let res: Response;
  try {
    res = await fetch(streamURL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
    });
  } catch {
    onError("Connection failed. Please check your network.");
    return;
  }

  if (!res.ok) {
    onError("AI service unavailable. Please try again.");
    return;
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = line.slice(6).trim();
      if (!data) continue;
      try {
        const event = JSON.parse(data);
        if (event.type === "token") onToken(event.content);
        else if (event.type === "done") onDone(event as ChatStreamMeta);
        else if (event.type === "error") onError(event.content ?? "Stream error");
      } catch {
        // malformed SSE line — skip
      }
    }
  }
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

export interface TranscribeResponse {
  transcript: string;
  language: string;
  agent_used: string;
}

export async function transcribeAudio(audioBlob: Blob): Promise<TranscribeResponse> {
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");
  const response = await api.post<TranscribeResponse>("/voice/transcribe", formData, {
    timeout: 60_000,
  });
  return response.data;
}

export interface TriageResponse {
  urgency_level: "critical" | "urgent" | "moderate" | "self-care" | string;
  severity_score: number;
  requires_escalation: boolean;
  escalation_path: string;
  immediate_action: string;
  reasoning: string;
  warning_signs: string[];
  next_steps: string[];
  confidence_score: number;
  agent_used: string;
  response: string;
  disclaimer: string;
  error?: string | null;
}

export interface MedicationItem {
  id: string;
  medication_name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date: string | null;
  notes: string | null;
  created_at: string;
}

export interface MedicationPayload {
  medication_name: string;
  dosage: string;
  frequency: string;
  start_date: string;
  end_date?: string | null;
  notes?: string | null;
}

export interface InteractionResult {
  risk_level: string;
  interactions: unknown[];
  contraindications: string[];
  warning_signs: string[];
  patient_response: string;
  disclaimer: string;
  confidence_score: number;
}

export interface ReportItem {
  id: string;
  filename: string;
  file_type: string;
  status: "processing" | "done" | "error";
  text_preview: string | null;
  page_count: number | null;
  error_message: string | null;
  created_at: string;
}

export interface DoctorMessage {
  id: string;
  patient_id: string;
  doctor_user_id: string;
  doctor_name: string;
  body: string;
  sender_role: "doctor" | "patient";
  is_read: boolean;
  created_at: string;
}

export interface MessageListResponse {
  items: DoctorMessage[];
  total: number;
  unread_count: number;
}

export async function uploadReport(file: File): Promise<ReportItem> {
  const form = new FormData();
  form.append("file", file);
  const response = await api.post<ReportItem>("/reports/upload", form);
  return response.data;
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
  submitFeedback: (chatId: string, feedback: "thumbs_up" | "thumbs_down") =>
    api.post("/chat/feedback", { chat_id: chatId, feedback }).then((r) => r.data),

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

  // Reports
  listReports: () =>
    api.get<{ items: ReportItem[]; total: number }>("/reports/").then((r) => r.data),
  deleteReport: (reportId: string) =>
    api.delete(`/reports/${reportId}`).then((r) => r.data),

  // Triage
  assessSymptoms: (symptoms: string) =>
    api.post<TriageResponse>("/triage/assess", { symptoms }).then((r) => r.data),

  // Medications
  listMedications: () =>
    api.get<{ items: MedicationItem[]; total: number }>("/medications/").then((r) => r.data),
  addMedication: (payload: MedicationPayload) =>
    api.post<MedicationItem>("/medications/", payload).then((r) => r.data),
  deleteMedication: (medicationId: string) =>
    api.delete(`/medications/${medicationId}`).then((r) => r.data),
  checkInteractions: () =>
    api.get<InteractionResult>("/medications/interactions").then((r) => r.data),

  // Patient messaging (inbox)
  getMessages: () =>
    api.get<MessageListResponse>("/messages/").then((r) => r.data),
  markMessageRead: (id: string) =>
    api.patch(`/messages/${id}/read`).then((r) => r.data),
  replyToDoctor: (doctorUserId: string, body: string) =>
    api.post<DoctorMessage>("/messages/reply", { doctor_user_id: doctorUserId, body }).then((r) => r.data),

  // Doctor messaging
  sendDoctorMessage: (patientId: string, body: string) =>
    api.post<DoctorMessage>(`/doctor/patients/${patientId}/messages`, { body }).then((r) => r.data),
  getDoctorMessages: (patientId: string) =>
    api.get<MessageListResponse>(`/doctor/patients/${patientId}/messages`).then((r) => r.data),
};
