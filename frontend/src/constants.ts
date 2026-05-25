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
  label: string;
  keywords: string[]; // 빈 배열 = 전체 (필터 없음)
}

export const SUBCATEGORIES: Record<number, Subcategory[]> = {
  1: [ // 음식점
    { label: '전체',   keywords: [] },
    { label: '한식',   keywords: ['한식'] },
    { label: '고기',   keywords: ['육류,고기'] },
    { label: '중식',   keywords: ['중국요리', '양꼬치'] },
    { label: '양식',   keywords: ['이탈리안', '피자', '햄버거', '스테이크,립', '멕시칸,브라질'] },
    { label: '일식',   keywords: ['초밥,롤', '일본식라면', '돈까스,우동', '일식집'] },
    { label: '면류',   keywords: ['일본식라면', '국수', '냉면', '돈까스,우동'] },
  ],
  2: [ // 카페
    { label: '전체',    keywords: [] },
    { label: '베이커리', keywords: ['제과,베이커리'] },
    { label: '테마카페', keywords: ['테마카페'] },
    { label: '커피',    keywords: ['커피전문점'] },
  ],
  3: [ // 쇼핑
    { label: '전체',    keywords: [] },
    { label: '의류',    keywords: ['의류판매'] },
    { label: '인테리어', keywords: ['인테리어장식판매'] },
    { label: '소품·잡화', keywords: ['패션잡화점', '디자인문구'] },
  ],
  4: [ // 바/펍
    { label: '전체',   keywords: [] },
    { label: '호프',   keywords: ['호프,요리주점'] },
    { label: '칵테일', keywords: ['칵테일바'] },
    { label: '이자카야', keywords: ['일본식주점'] },
    { label: '와인바', keywords: ['와인바'] },
    { label: '포장마차', keywords: ['실내포장마차'] },
  ],
  5: [ // 전시/문화
    { label: '전체',  keywords: [] },
    { label: '공연',  keywords: ['공연장,연극극장'] },
    { label: '전시',  keywords: ['전시관'] },
    { label: '미술관', keywords: ['미술관'] },
  ],
};
