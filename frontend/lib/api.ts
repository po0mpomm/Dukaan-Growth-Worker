import { RunStatus, ResultObject } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "";

export async function createRun(formData: FormData): Promise<{ run_id: string; status: string }> {
  const res = await fetch(`${BASE_URL}/api/runs`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Failed to start run: ${res.status} ${errorText}`);
  }
  return res.json();
}

export async function getRunStatus(runId: string): Promise<RunStatus> {
  const res = await fetch(`${BASE_URL}/api/runs/${runId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch run status: ${res.status}`);
  }
  return res.json();
}

export async function getRunResult(runId: string): Promise<{ result?: ResultObject; escalation?: any }> {
  const res = await fetch(`${BASE_URL}/api/runs/${runId}/result`);
  if (!res.ok) {
    throw new Error(`Failed to fetch run result: ${res.status}`);
  }
  return res.json();
}

export async function markActionDone(runId: string, actionN: number): Promise<{ success: boolean }> {
  const res = await fetch(`${BASE_URL}/api/runs/${runId}/actions/${actionN}/done`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to mark action done: ${res.status}`);
  }
  return res.json();
}

export async function getExportPreview(runId: string): Promise<{
  payload: any;
  payload_hash: string;
  payload_json: string;
  notice_version: string;
}> {
  const res = await fetch(`${BASE_URL}/api/runs/${runId}/export/preview`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error(`Failed to generate export preview: ${res.status}`);
  }
  return res.json();
}

export async function submitConsent(
  runId: string,
  payloadHash: string,
  noticeVersion: string
): Promise<{ status: string; outbox_id: string }> {
  const res = await fetch(`${BASE_URL}/api/runs/${runId}/export/consent`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ payload_hash: payloadHash, notice_version: noticeVersion }),
  });
  if (!res.ok) {
    throw new Error(`Failed to submit consent: ${res.status}`);
  }
  return res.json();
}

export async function verifyAuditChain(): Promise<{
  valid: boolean;
  event_count: number;
  head_hash: string;
  tampered_at_seq?: number;
  error?: string;
}> {
  const res = await fetch(`${BASE_URL}/api/audit/verify`);
  if (!res.ok) {
    throw new Error(`Failed to verify audit chain: ${res.status}`);
  }
  return res.json();
}

export async function deleteAllData(): Promise<{ status: string; message_en: string; message_hi: string }> {
  const res = await fetch(`${BASE_URL}/api/data`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(`Failed to delete data: ${res.status}`);
  }
  return res.json();
}
