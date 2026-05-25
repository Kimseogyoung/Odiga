export const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export const CATEGORY_LABEL: Record<number, string> = {
  1: '음식점',
  2: '카페',
  3: '쇼핑',
  4: '바/펍',
  5: '전시/문화',
};

export const CATEGORY_EMOJI: Record<number, string> = {
  1: '🍽',
  2: '☕',
  3: '🛍',
  4: '🍺',
  5: '🎨',
};

export const CATEGORY_EMOJI_FALLBACK = '📍';

export interface Subcategory {
  id: number | null; // null = 전체 (필터 없음)
  label: string;
}

export const SUBCATEGORIES: Record<number, Subcategory[]> = {
  1: [ // 음식점
    { id: null, label: '전체' },
    { id: 101,  label: '한식' },
    { id: 102,  label: '고기' },
    { id: 103,  label: '중식' },
    { id: 104,  label: '양식' },
    { id: 105,  label: '일식' },
    { id: 106,  label: '면류' },
  ],
  2: [ // 카페
    { id: null, label: '전체' },
    { id: 201,  label: '베이커리' },
    { id: 202,  label: '테마카페' },
    { id: 203,  label: '커피' },
  ],
  3: [ // 쇼핑
    { id: null, label: '전체' },
    { id: 301,  label: '의류' },
    { id: 302,  label: '인테리어' },
    { id: 303,  label: '소품·잡화' },
  ],
  4: [ // 바/펍
    { id: null, label: '전체' },
    { id: 401,  label: '호프' },
    { id: 402,  label: '칵테일' },
    { id: 403,  label: '이자카야' },
    { id: 404,  label: '와인바' },
    { id: 405,  label: '포장마차' },
  ],
  5: [ // 전시/문화
    { id: null, label: '전체' },
    { id: 501,  label: '공연' },
    { id: 502,  label: '전시' },
    { id: 503,  label: '미술관' },
  ],
};
