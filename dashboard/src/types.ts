/* TypeScript interfaces matching the FastAPI response schemas */

export interface MessageStats {
  sent: number;
  received: number;
}

export interface CallStats {
  incoming: number;
  outgoing: number;
  missed: number;
  total_seconds: number;
}

export interface HurtfulItem {
  time: string;
  words: string[];
  severity: string;
  preview: string;
  source: string;
}

export interface PatternItem {
  time: string;
  pattern: string;
  matched: string;
  message: string;
  source: string;
}

export interface DaySummary {
  date: string;
  weekday: string;
  had_contact: boolean;
  messages: MessageStats;
  calls: CallStats;
  hurtful_from_user: HurtfulItem[];
  hurtful_from_contact: HurtfulItem[];
  patterns_from_user: PatternItem[];
  patterns_from_contact: PatternItem[];
}

export interface GapItem {
  start: string;
  end: string;
  days: number;
  reason: string;
}

export interface CaseInfo {
  case_id: string;
  case_name: string;
  user_label: string;
  contact_label: string;
  period_start: string;
  period_end: string;
  generated: string;
  total_days: number;
  has_data: boolean;
}

export interface SummaryResponse {
  case_name: string;
  user_label: string;
  contact_label: string;
  period: { start: string; end: string };
  generated: string;
  total_days: number;
  contact_days: number;
  no_contact_days: number;
  total_messages_sent: number;
  total_messages_received: number;
  total_calls: number;
  total_talk_seconds: number;
  hurtful_from_user: number;
  hurtful_from_contact: number;
  severity_breakdown: Record<string, Record<string, number>>;
  pattern_counts_user: Record<string, number>;
  pattern_counts_contact: Record<string, number>;
}

export interface TimelineResponse {
  days: DaySummary[];
  gaps: GapItem[];
}

export interface PatternDetail {
  pattern: string;
  label: string;
  total_user: number;
  total_contact: number;
  instances: PatternItem[];
}

export interface PatternsResponse {
  patterns: PatternDetail[];
}

export interface HurtfulResponse {
  from_user: HurtfulItem[];
  from_contact: HurtfulItem[];
}
