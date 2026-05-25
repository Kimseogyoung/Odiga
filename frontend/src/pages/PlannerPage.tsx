import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { getCandidates, pickPlace, getConstants } from '../api/courses';
import PlaceCard from '../components/PlaceCard';
import type { PlaceCandidate, SlotInfo, Constants } from '../types';

const DEFAULT_CATEGORIES: Record<number, string> = {
  1: '음식점',
  2: '카페',
  3: '쇼핑',
  4: '바/펍',
  5: '전시/문화',
};

interface LocationState {
  total_slots: number;
  slot: SlotInfo;
}

export default function PlannerPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const state = location.state as LocationState | null;

  const [slot, setSlot] = useState<SlotInfo | null>(state?.slot ?? null);
  const [totalSlots] = useState(state?.total_slots ?? 1);
  const [categoryId, setCategoryId] = useState<number>(1);
  const [candidates, setCandidates] = useState<PlaceCandidate[]>([]);
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [picking, setPicking] = useState(false);
  const [error, setError] = useState('');
  const [constants, setConstants] = useState<Constants | null>(null);

  useEffect(() => {
    getConstants().then(setConstants).catch(() => {});
  }, []);

  const categories = constants?.categories ?? DEFAULT_CATEGORIES;

  async function handleFetchCandidates() {
    if (!sessionId) return;
    setError('');
    setLoadingCandidates(true);
    setCandidates([]);
    try {
      const res = await getCandidates(sessionId, categoryId);
      if (res.candidates.length === 0) {
        setError('후보 장소가 없습니다. 다른 카테고리를 선택해 보세요.');
      }
      setCandidates(res.candidates);
    } catch {
      setError('후보 장소를 불러오지 못했습니다.');
    } finally {
      setLoadingCandidates(false);
    }
  }

  async function handlePick(place: PlaceCandidate) {
    if (!sessionId || picking) return;
    setPicking(true);
    setError('');
    try {
      const res = await pickPlace(sessionId, place.kakao_place_id);
      if (res.done && res.share_token) {
        navigate(`/course/${res.share_token}`);
      } else if (!res.done && res.slot) {
        setSlot(res.slot);
        setCandidates([]);
        setCategoryId(1);
      }
    } catch {
      setError('선택 처리 중 오류가 발생했습니다.');
    } finally {
      setPicking(false);
    }
  }

  if (!slot) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-400">세션 정보가 없습니다. 처음부터 다시 시작해주세요.</p>
      </div>
    );
  }

  const currentSlotNum = slot.slot_index + 1;
  const progressPct = Math.round(((currentSlotNum - 1) / totalSlots) * 100);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-8 px-4">
      <div className="w-full max-w-md flex flex-col gap-5">
        {/* 진행 상황 */}
        <div className="bg-white rounded-2xl p-4 shadow-sm">
          <div className="flex justify-between text-sm text-gray-500 mb-2">
            <span>슬롯 {currentSlotNum} / {totalSlots}</span>
            <span>남은 시간 {slot.remaining_minutes}분</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-2">
            <div
              className="bg-black h-2 rounded-full transition-all"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <p className="mt-2 text-center font-bold text-gray-800">
            {slot.scheduled_time} 출발
          </p>
        </div>

        {/* 카테고리 선택 */}
        <section className="bg-white rounded-2xl p-5 shadow-sm">
          <h2 className="text-sm font-bold text-gray-500 mb-3">어떤 곳에 갈까요?</h2>
          <div className="flex flex-wrap gap-2 mb-4">
            {Object.entries(categories).map(([id, label]) => (
              <button
                key={id}
                onClick={() => {
                  setCategoryId(Number(id));
                  setCandidates([]);
                }}
                className={`px-3 py-2 rounded-xl text-sm font-semibold transition ${
                  categoryId === Number(id)
                    ? 'bg-black text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <button
            onClick={handleFetchCandidates}
            disabled={loadingCandidates}
            className="w-full py-3 bg-gray-900 text-white text-sm font-bold rounded-xl hover:bg-gray-700 active:scale-95 transition disabled:opacity-50"
          >
            {loadingCandidates ? '검색 중…' : '장소 찾기'}
          </button>
        </section>

        {error && <p className="text-red-500 text-sm text-center">{error}</p>}

        {/* 후보 장소 */}
        {candidates.length > 0 && (
          <section className="flex flex-col gap-4">
            <h2 className="text-sm font-bold text-gray-500">추천 장소 {candidates.length}곳</h2>
            {candidates.map((place) => (
              <PlaceCard
                key={place.kakao_place_id}
                place={place}
                onSelect={handlePick}
                disabled={picking}
              />
            ))}
          </section>
        )}
      </div>
    </div>
  );
}
