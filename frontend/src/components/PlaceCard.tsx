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
    <div
      className="bg-white rounded-[18px] overflow-hidden flex"
      style={{ boxShadow: '0 2px 10px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.04)' }}
    >
      {/* 이미지 */}
      <div
        className="w-20 shrink-0 self-stretch flex items-center justify-center text-4xl"
        style={{ background: 'linear-gradient(135deg, #FFFBEA 0%, #FFF3C0 100%)' }}
      >
        {place.photo_url ? (
          <img src={place.photo_url} alt={place.name} className="w-full h-full object-cover" />
        ) : (
          <span>{CATEGORY_EMOJI[place.category_id] ?? CATEGORY_EMOJI_FALLBACK}</span>
        )}
      </div>

      {/* 정보 */}
      <div className="flex-1 py-3 px-3.5 flex flex-col gap-1 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-bold truncate">{place.name}</h3>
          {categoryLabel && (
            <span
              className="shrink-0 text-[10px] font-bold px-[9px] py-[3px] rounded-full whitespace-nowrap"
              style={{ background: '#FFFBEA', color: '#B8860B' }}
            >
              {categoryLabel}
            </span>
          )}
        </div>

        <p className="text-[11px] truncate" style={{ color: '#BBBBBB' }}>{place.address}</p>

        {place.walk_minutes_from_prev !== null && (
          <p className="text-[11px] font-semibold" style={{ color: '#B8860B' }}>
            🚶 도보 약 {place.walk_minutes_from_prev}분
          </p>
        )}

        {review && (
          <p className="text-xs line-clamp-2 leading-relaxed" style={{ color: '#666' }}>{review}</p>
        )}

        {place.caution && (
          <p className="text-[10px] text-amber-600 bg-amber-50 rounded px-2 py-0.5 line-clamp-1">
            ⚠ {place.caution}
          </p>
        )}

        <div className="flex items-center justify-between mt-1">
          {place.kakao_url ? (
            <a
              href={place.kakao_url}
              target="_blank"
              rel="noreferrer"
              className="text-[11px] font-semibold"
              style={{ color: '#B8860B' }}
              onClick={(e) => e.stopPropagation()}
            >
              카카오맵 →
            </a>
          ) : (
            <span />
          )}
          <button
            onClick={() => onSelect(place)}
            disabled={disabled}
            className="px-3.5 py-[7px] rounded-full text-xs font-bold transition active:scale-95 disabled:opacity-40"
            style={{
              background: '#FFD663',
              color: '#1A1A1A',
              boxShadow: '0 2px 8px rgba(255,214,99,0.45)',
            }}
          >
            여기 갈래요 ✓
          </button>
        </div>
      </div>
    </div>
  );
}
