export type WorkflowState =
  | "S0_RECEIVED"
  | "S1_VALIDATING"
  | "S2_ANALYZING"
  | "S3_PHRASING"
  | "S4_CHECKING"
  | "S5_REVIEW"
  | "S6_SAVING"
  | "S7_SHARING"
  | "S_DONE"
  | "S_ESCALATED"
  | "S_ERROR";

export type ValidationOutcome = "PROCEED" | "PROCEED_WITH_CAVEAT" | "ESCALATE";

export interface CompletenessResult {
  score: number;
  day_coverage: number;
  expense_coverage: number;
  udhaar_integrity: number;
  flagged_row_ratio: number;
  block_checks_failed: string[];
  warn_checks: string[];
  outcome: ValidationOutcome;
}

export interface WeakArea {
  rule_id: string; // W1..W7
  title_en: string;
  title_hi: string;
  metrics: Record<string, any>;
  rupee_impact: number;
  rank: number;
  title?: string;
  evidence?: string;
  recommended_action?: string;
}

export interface FollowUp {
  rank: number;
  alias: string;
  score: number;
  reason_code: string;
  reason_en: string;
  reason_hi: string;
  outstanding_amount?: number;
  days_overdue?: number;
  is_lapsed_regular: boolean;
}

export interface ActionItem {
  n: number;
  action_id?: string;
  title: string;
  why: string;
  description?: string;
  first_step: string;
  language: "en" | "hi";
  source: "model" | "template";
  rule_id: string;
  done: boolean;
  rationale?: string;
  estimated_impact?: string;
}

export interface MoMComparison {
  has_prior_month: boolean;
  prior_month?: string;
  sales_change_pct?: number;
  credit_share_change_pct?: number;
  overdue_change_pct?: number;
  rules_resolved: string[];
  rules_new: string[];
  actions_completed: number;
  actions_total: number;
}

export interface ResultObject {
  run_id: string;
  month: string;
  language: "en" | "hi";
  completeness: CompletenessResult;
  verdict_en: string;
  verdict_hi: string;
  weak_areas: WeakArea[];
  actions: ActionItem[];
  followups: FollowUp[];
  comparison?: MoMComparison;
  has_caveat: boolean;
  caveat_en?: string;
  caveat_hi?: string;
  model_used: boolean;
  created_at: string;
  metrics?: Record<string, any>;
}

export interface EscalationResult {
  run_id: string;
  reason_code: string;
  reason_en: string;
  reason_hi: string;
  questions: string[];
  completeness?: CompletenessResult;
}

export interface RunStatus {
  run_id: string;
  state: WorkflowState;
  progress_pct: number;
  message_en: string;
  message_hi: string;
  result?: ResultObject;
  escalation?: EscalationResult;
  error_message?: string;
}

export interface AggregateExportPayload {
  schema_version: string;
  shop_pid: string;
  month: string;
  region_type: "urban" | "semi_urban" | "rural" | "deep_rural";
  sales_change_band: string;
  credit_share_band: string;
  overdue_band: string;
  rules_fired: string[];
  completeness_band: string;
  action_completion_band: string;
}
