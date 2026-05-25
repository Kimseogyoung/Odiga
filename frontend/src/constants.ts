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
