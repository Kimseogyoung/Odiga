import { CATEGORY_EMOJI, CATEGORY_EMOJI_FALLBACK } from '../constants';
import type { PlaceCandidate } from '../types';

function formatCategory(kakaoCategory: string): string {
  if (!kakaoCategory) return '';
  const parts = kakaoCategory.split(' > ');
  return parts.slice(-2).join(' · ');
}

interface Props {
  place: PlaceCandidate;
  onSelect: (place: PlaceCandidate) => void;
  disabled?: boolean;
}

export default function PlaceCard({ place, onSelect, disabled }: Props) {
  const categoryLabel = formatCategory(place.kakao_category);
  const review = place.summary || place.blog_review;

  return (
    <div className="bg-white rounded-2xl shadow-md overflow-hidden border border-gray-100">
      <div className="h-28 bg-gray-100 flex items-center justify-center text-5xl">
        {CATEGORY_EMOJI[place.category_id] ?? CATEGORY_EMOJI_FALLBACK}
      </div>
      <div className="p-4 flex flex-col gap-2">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-bold text-gray-900 text-base leading-tight">{place.name}</h3>
          {categoryLabel && (
            <span className="shrink-0 text-xs text-gray-400 bg-gray-50 rounded-full px-2 py-0.5">
              {categoryLabel}
            </span>
          )}
        </div>
        <p className="text-xs text-gray-400 line-clamp-1">{place.address}</p>
        {/* summary: AI 요약(정식), blog_review: 블로그 원문 앞 150자 (임시 fallback — 추후 AI 요약으로 대체 예정) */}
        {review && (
          <p className="text-sm text-gray-600 line-clamp-3 leading-relaxed">{review}</p>
        )}
        {place.caution && (
          <p className="text-xs text-amber-600 bg-amber-50 rounded px-2 py-1 line-clamp-1">
            ⚠ {place.caution}
          </p>
        )}
        <div className="flex items-center justify-between mt-1">
          {place.kakao_url ? (
            <a
              href={place.kakao_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-blue-400 hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              카카오맵
            </a>
          ) : <span />}
          <button
            onClick={() => onSelect(place)}
            disabled={disabled}
            className="px-4 py-2 bg-black text-white text-sm font-semibold rounded-xl hover:bg-gray-800 active:scale-95 transition disabled:opacity-40"
          >
            여기로 결정
          </button>
        </div>
      </div>
    </div>
  );
}
