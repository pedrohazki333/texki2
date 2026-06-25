import type { ApiErrorBody } from "@/lib/tipos";

const API_BASE = "/api";

export type ApiResult<T> =
  | { ok: true; status: number; data: T }
  | { ok: false; status: number; error: ApiErrorBody["error"] };

export async function apiClientFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<ApiResult<T>> {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    ...init,
  });

  if (res.status === 204) {
    return { ok: true, status: 204, data: undefined as T };
  }

  const body = await res.json().catch(() => null);

  if (!res.ok) {
    const error =
      (body as ApiErrorBody | null)?.error ?? {
        code: "http.error",
        message: "Erro inesperado.",
        details: [],
      };
    return { ok: false, status: res.status, error };
  }

  return { ok: true, status: res.status, data: body as T };
}
