const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    public data: unknown,
  ) {
    super(`API error ${status}`);
  }
}

export async function apiPost<T>(path: string, body: object): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

export async function apiPostForm<T>(
  path: string,
  form: FormData,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    body: form, // no Content-Type header — let browser set multipart boundary
  });
  const data = await res.json();
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}

export async function apiGet<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`);
  const data = await res.json();
  if (!res.ok) throw new ApiError(res.status, data);
  return data as T;
}
