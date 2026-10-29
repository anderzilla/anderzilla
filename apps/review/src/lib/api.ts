export type Comment = { id: string; round: number; collection: string; recordId: string; field: string | null; text: string; author: string; createdAt: string; resolved: boolean };
export type Item = { collection: 'content' | 'media' | 'banners' | string; id: string; version: number; status: string; data: Record<string, any> };
export type Media = { id: string; altPT?: string; credit?: string; imageDataUrl?: string | null };
export type Submission = { id: string; status: 'pending' | 'changes_requested' | 'approved' | 'rejected' | 'published'; round: number; note: string; agentName?: string; agentId: string; records: { collection: string; id: string; version: number }[]; releaseId: string | null; createdAt: string; updatedAt: string };
export type Detail = { submission: Submission; items: Item[]; referencedMedia: Media[]; comments: Comment[] };
export type PreviewState = { state: 'none' | 'building' | 'ready' | 'failed' | 'unavailable'; error?: string; builtAt?: string; active?: boolean; round?: string };

export const apiBase = (process.env.NEXT_PUBLIC_REVIEW_API_BASE || '').replace(/\/$/, '');
export const previewUrl = (process.env.NEXT_PUBLIC_REVIEW_PREVIEW_URL || 'http://127.0.0.1:8789').replace(/\/$/, '');

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, token: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(apiBase + path, {
    ...init,
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...init.headers },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new ApiError(response.status, payload.error?.message || `Operação recusada (${response.status}).`);
  return payload as T;
}

export const statusLabel: Record<string, string> = {
  pending: 'Aguardando revisão',
  changes_requested: 'Correções pedidas',
  approved: 'Aprovado · release em homolog',
  rejected: 'Recusado',
  published: 'Publicado',
};

export const collectionLabel: Record<string, string> = { content: 'Notícia', media: 'Imagem', banners: 'Banner' };

export function parseSources(value: unknown): { name: string; url: string; note?: string }[] {
  try {
    const list = JSON.parse(String(value || '[]'));
    return Array.isArray(list) ? list.filter((row) => row && typeof row.url === 'string' && typeof row.name === 'string') : [];
  } catch {
    return [];
  }
}

/** Only internal paths and HTTPS links become clickable; anything else is shown as plain text. */
export function safeHref(value: unknown): string | null {
  const text = String(value || '');
  if (text.startsWith('/') && !text.startsWith('//')) return text;
  try {
    return new URL(text).protocol === 'https:' ? text : null;
  } catch {
    return null;
  }
}
