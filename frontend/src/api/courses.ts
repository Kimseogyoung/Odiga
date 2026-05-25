import type {
  Constants,
  CreateSessionResponse,
  CandidatesResponse,
  PickResponse,
  CourseResponse,
} from '../types';

const BASE = 'http://localhost:8000';

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export function getConstants(): Promise<Constants> {
  return request<Constants>('/api/constants');
}

export function createSession(body: {
  region_id: number;
  keyword_ids: number[];
  start_time: string;
  end_time: string;
  headcount?: number;
  budget?: number;
}): Promise<CreateSessionResponse> {
  return request<CreateSessionResponse>('/api/courses/session', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export function getCandidates(
  sessionId: string,
  categoryId: number,
): Promise<CandidatesResponse> {
  return request<CandidatesResponse>(
    `/api/courses/session/${sessionId}/candidates`,
    { method: 'POST', body: JSON.stringify({ category_id: categoryId }) },
  );
}

export function pickPlace(
  sessionId: string,
  kakaoPlaceId: string,
): Promise<PickResponse> {
  return request<PickResponse>(
    `/api/courses/session/${sessionId}/pick`,
    { method: 'POST', body: JSON.stringify({ kakao_place_id: kakaoPlaceId }) },
  );
}

export function getCourse(shareToken: string): Promise<CourseResponse> {
  return request<CourseResponse>(`/api/courses/${shareToken}`);
}
