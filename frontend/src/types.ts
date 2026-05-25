export interface SlotInfo {
  slot_index: number;
  scheduled_time: string;
  remaining_minutes: number;
}

export interface PlaceCandidate {
  kakao_place_id: string;
  name: string;
  address: string;
  category_id: number;
  lat: number;
  lng: number;
  kakao_url: string;
  summary: string;
  caution: string;
  photo_url: string | null;
}

export interface CourseItem {
  order: number;
  scheduled_time: string;
  stay_minutes: number;
  travel_time_to_next_minutes: number;
  place: PlaceCandidate;
}

export interface CourseResponse {
  share_token: string;
  region_id: number;
  keyword_ids: number[];
  start_time: string;
  end_time: string;
  headcount: number | null;
  budget: number | null;
  items: CourseItem[];
}

export interface CreateSessionResponse {
  session_id: string;
  total_slots: number;
  slot: SlotInfo;
}

export interface CandidatesResponse {
  candidates: PlaceCandidate[];
}

export interface PickResponse {
  done: boolean;
  slot: SlotInfo | null;
  share_token: string | null;
}

export interface Constants {
  regions: Record<number, string>;
  keywords: Record<number, string>;
  categories: Record<number, string>;
}
