import { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { getCandidates, pickPlace, getConstants } from '../api/courses';
import PlaceCard from '../components/PlaceCard';
import { CATEGORY_LABEL, SUBCATEGORIES } from '../constants';
import type { PlaceCandidate, SlotInfo, Constants } from '../types';

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
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [subcategoryId, setSubcategoryId] = useState<number | null>(null);
  const [candidateCache, setCandidateCache] = useState<Record<string, PlaceCandidate[]>>({});
  const [loadingCandidates, setLoadingCandidates] = useState(false);
  const [picking, setPicking] = useState(false);
  const [error, setError] = useState('');
  const [refreshCooldown, setRefreshCooldown] = useState(0);
  const [seenIds, setSeenIds] = useState<string[]>([]);

  const cacheKey = categoryId !== null ? `${categoryId}_${subcategoryId ?? 'all'}` : '';
  const candidates = cacheKey ? (candidateCache[cacheKey] ?? []) : [];
  const [constants, setConstants] = useState<Constants | null>(null);

  useEffect(() => {
    getConstants().then(setConstants).catch(() => {});
  }, []);

  const categories = constants?.categories ?? CATEGORY_LABEL;

  async function handleFetchCandidates(
    extraExcludeIds: string[] = [],
    catId?: number,
    subId?: number | null,
  ) {
    if (!sessionId) return;
    const targetCatId = catId ?? categoryId;
    if (targetCatId === null) return;
    const targetSubId = subId !== undefined ? subId : subcategoryId;
    const key = `${targetCatId}_${targetSubId ?? 'all'}`;

    if (extraExcludeIds.length === 0 && (candidateCache[key]?.length ?? 0) > 0) {
      setCategoryId(targetCatId);
      setSubcategoryId(targetSubId);
      return;
    }

    setError('');
    setLoadingCandidates(true);
    try {
      const res = await getCandidates(sessionId, targetCatId, extraExcludeIds, targetSubId);
      if (res.candidates.length === 0) {
        setError('해당 조건의 장소가 없습니다. 다른 항목을 선택해 보세요.');
      }
      setCandidateCache((prev) => ({ ...prev, [key]: res.candidates }));
      setSeenIds((prev) => [...prev, ...res.candidates.map((c) => c.kakao_place_id)]);
    } catch {
      setError('후보 장소를 불러오지 못했습니다.');
    } finally {
      setLoadingCandidates(false);
    }
  }

  async function handleRefresh() {
    if (refreshCooldown > 0 || loadingCandidates) return;
    setRefreshCooldown(3);
    const timer = setInterval(() => {
      setRefreshCooldown((prev) => {
        if (prev <= 1) { clearInterval(timer); return 0; }
        return prev - 1;
      });
    }, 1000);
    await handleFetchCandidates(seenIds, undefined, subcategoryId);
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
        setCandidateCache({});
        setCategoryId(null);
        setSubcategoryId(null);
        setSeenIds([]);
      }
    } catch {
      setError('선택 처리 중 오류가 발생했습니다.');
    } finally {
      setPicking(false);
    }
  }

  if (!slot) {
    return (
      <div className="min-h-[100svh] flex items-center justify-center">
        <p style={{ color: '#888' }}>세션 정보가 없습니다. 처음부터 다시 시작해주세요.</p>
      </div>
    );
  }

  const currentSlotNum = slot.slot_index + 1;
  const progressPct = Math.round(((currentSlotNum - 1) / totalSlots) * 100);

  return (
    <div className="min-h-[100svh] max-w-[480px] mx-auto pb-10" style={{ background: '#FAFAF8', color: '#1A1A1A' }}>

      {/* 상단 네비 바 */}
      <div
        className="sticky top-0 z-50 bg-white flex items-center justify-between px-5 py-3"
        style={{ borderBottom: '1px solid #F0F0F0' }}
      >
        <button
          onClick={() => navigate(-1)}
          className="w-9 h-9 rounded-full flex items-center justify-center text-base cursor-pointer"
          style={{ background: '#F4F4F0', border: 'none' }}
        >
          ←
        </button>
        <span className="text-[15px] font-extrabold tracking-tight">코스 만드는 중</span>
        <div className="w-9" />
      </div>

      {/* 진행 카드 */}
      <div
        className="px-5 py-4"
        style={{ background: '#FFFBEA', borderBottom: '1px solid rgba(255,214,99,0.3)' }}
      >
        <div className="flex justify-between items-center mb-2.5">
          <span className="text-[13px] font-bold" style={{ color: '#B8860B' }}>
            코스 {currentSlotNum} / {totalSlots}
          </span>
          <span className="text-[12px] font-semibold" style={{ color: 'rgba(184,134,11,0.8)' }}>
            남은 시간 {slot.remaining_minutes}분
          </span>
        </div>
        <div className="h-[7px] rounded-full overflow-hidden" style={{ background: 'rgba(255,214,99,0.25)' }}>
          <div
            className="h-full rounded-full transition-all"
            style={{ width: `${progressPct}%`, background: '#FFD663' }}
          />
        </div>
        <p className="mt-2.5 text-center text-sm font-extrabold" style={{ color: '#B8860B' }}>
          {slot.scheduled_time} 출발 🚀 · 지금은 {currentSlotNum}번째 장소 고르는 중
        </p>
      </div>

      {/* 카테고리 칩 */}
      <div
        className="flex gap-2 px-5 py-3.5 scrollbar-none overflow-x-auto"
        style={{ borderBottom: '1px solid #F0F0F0' }}
      >
        {Object.entries(categories).map(([id, label]) => (
          <button
            key={id}
            onClick={() => {
              const newId = Number(id);
              setCategoryId(newId);
              setSubcategoryId(null);
              handleFetchCandidates([], newId, null);
            }}
            className="shrink-0 px-4 py-[9px] rounded-full text-[13px] font-bold transition cursor-pointer"
            style={
              categoryId === Number(id)
                ? { background: '#FFD663', color: '#1A1A1A', boxShadow: '0 2px 8px rgba(255,214,99,0.4)', border: 'none' }
                : { background: '#F4F4F0', color: '#888', border: 'none' }
            }
          >
            {label}
          </button>
        ))}
      </div>

      {/* 서브카테고리 칩 */}
      {categoryId !== null && (SUBCATEGORIES[categoryId]?.length ?? 0) > 1 && (
        <div
          className="flex gap-2 px-5 py-2.5 scrollbar-none overflow-x-auto"
          style={{ borderBottom: '1px solid #F0F0F0' }}
        >
          {SUBCATEGORIES[categoryId].map((sub) => (
            <button
              key={sub.id ?? 'all'}
              onClick={() => {
                setSubcategoryId(sub.id);
                handleFetchCandidates([], categoryId, sub.id);
              }}
              className="shrink-0 px-3 py-1.5 rounded-full text-xs font-bold transition cursor-pointer"
              style={
                subcategoryId === sub.id
                  ? { background: '#FFD663', color: '#1A1A1A', border: 'none' }
                  : { background: '#F4F4F0', color: '#888', border: 'none' }
              }
            >
              {sub.label}
            </button>
          ))}
        </div>
      )}

      {/* 본문 */}
      <div className="px-5 py-3.5 flex flex-col gap-3">
        {loadingCandidates && (
          <p className="text-center text-sm" style={{ color: '#BBBBBB' }}>검색 중…</p>
        )}
        {error && <p className="text-red-500 text-sm text-center">{error}</p>}

        {candidates.length > 0 && (
          <>
            <p className="text-xs font-bold" style={{ color: '#BBBBBB', letterSpacing: '0.3px' }}>
              추천 장소 {candidates.length}곳
            </p>
            {candidates.map((place) => (
              <PlaceCard
                key={place.kakao_place_id}
                place={place}
                onSelect={handlePick}
                disabled={picking}
              />
            ))}
            <button
              onClick={handleRefresh}
              disabled={refreshCooldown > 0 || loadingCandidates}
              className="w-full py-3.5 rounded-full text-[13px] font-bold transition disabled:opacity-40 cursor-pointer"
              style={{
                background: 'white',
                border: '1.5px solid #F0F0F0',
                color: '#888',
              }}
            >
              {refreshCooldown > 0 ? `다른 장소 더 보기 (${refreshCooldown}초)` : '다른 장소 더 보기'}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
