import { CATEGORY_EMOJI, CATEGORY_EMOJI_FALLBACK } from '../constants';
import type { PlaceCandidate } from '../types';

interface Props {
  place: PlaceCandidate;
  onSelect: (place: PlaceCandidate) => void;
  disabled?: boolean;
}

export default function PlaceCard({ place, onSelect, disabled }: Props) {
  return (
    <div className="bg-white rounded-2xl shadow-md overflow-hidden border border-gray-100">
      <div className="h-36 bg-gray-100 flex items-center justify-center text-5xl">
        {CATEGORY_EMOJI[place.category_id] ?? CATEGORY_EMOJI_FALLBACK}
      </div>
      <div className="p-4 flex flex-col gap-2">
        <h3 className="font-bold text-gray-900 text-base leading-tight">{place.name}</h3>
        <p className="text-xs text-gray-500 line-clamp-1">{place.address}</p>
        {place.summary && (
          <p className="text-sm text-gray-700 line-clamp-2">{place.summary}</p>
        )}
        {place.caution && (
          <p className="text-xs text-amber-600 bg-amber-50 rounded px-2 py-1 line-clamp-1">
            ⚠ {place.caution}
          </p>
        )}
        <div className="flex gap-2 mt-1">
          {place.kakao_url && (
            <a
              href={place.kakao_url}
              target="_blank"
              rel="noreferrer"
              className="text-xs text-blue-500 hover:underline"
              onClick={(e) => e.stopPropagation()}
            >
              카카오맵
            </a>
          )}
        </div>
        <button
          onClick={() => onSelect(place)}
          disabled={disabled}
          className="mt-1 w-full py-2 bg-black text-white text-sm font-semibold rounded-xl hover:bg-gray-800 active:scale-95 transition disabled:opacity-40"
        >
          여기로 결정
        </button>
      </div>
    </div>
  );
}
