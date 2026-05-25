import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getConstants, createSession } from '../api/courses';
import type { Constants } from '../types';

export default function HomePage() {
  const navigate = useNavigate();
  const [constants, setConstants] = useState<Constants | null>(null);
  const [regionId, setRegionId] = useState<number>(1);
  const [keywordIds, setKeywordIds] = useState<number[]>([]);
  const [startTime, setStartTime] = useState('12:00');
  const [endTime, setEndTime] = useState('18:00');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getConstants().then(setConstants).catch(() => setError('서버에 연결할 수 없습니다.'));
  }, []);

  function toggleKeyword(id: number) {
    setKeywordIds((prev) =>
      prev.includes(id) ? prev.filter((k) => k !== id) : [...prev, id],
    );
  }

  async function handleStart() {
    if (keywordIds.length === 0) {
      setError('키워드를 최소 1개 선택하세요.');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await createSession({
        region_id: regionId,
        keyword_ids: keywordIds,
        start_time: startTime,
        end_time: endTime,
      });
      navigate(`/planner/${res.session_id}`, {
        state: { total_slots: res.total_slots, slot: res.slot },
      });
    } catch {
      setError('세션 생성 실패. 서버를 확인하세요.');
    } finally {
      setLoading(false);
    }
  }

  if (!constants) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-400">{error || '로딩 중…'}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10 px-4">
      <div className="w-full max-w-md flex flex-col gap-6">
        {/* 헤더 */}
        <div className="text-center">
          <h1 className="text-3xl font-black tracking-tight text-gray-900">오디가</h1>
          <p className="text-gray-500 mt-1 text-sm">서울 하루 코스 플래너</p>
        </div>

        {/* 지역 */}
        <section className="bg-white rounded-2xl p-5 shadow-sm">
          <h2 className="text-sm font-bold text-gray-500 mb-3 uppercase tracking-wide">지역</h2>
          <div className="flex gap-2">
            {Object.entries(constants.regions).map(([id, label]) => (
              <button
                key={id}
                onClick={() => setRegionId(Number(id))}
                className={`flex-1 py-3 rounded-xl text-sm font-bold transition ${
                  regionId === Number(id)
                    ? 'bg-black text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </section>

        {/* 키워드 */}
        <section className="bg-white rounded-2xl p-5 shadow-sm">
          <h2 className="text-sm font-bold text-gray-500 mb-3 uppercase tracking-wide">
            키워드 <span className="normal-case font-normal text-gray-400">(복수 선택)</span>
          </h2>
          <div className="flex flex-wrap gap-2">
            {Object.entries(constants.keywords).map(([id, label]) => {
              const selected = keywordIds.includes(Number(id));
              return (
                <button
                  key={id}
                  onClick={() => toggleKeyword(Number(id))}
                  className={`px-3 py-1.5 rounded-full text-sm font-medium transition ${
                    selected
                      ? 'bg-black text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </section>

        {/* 시간 */}
        <section className="bg-white rounded-2xl p-5 shadow-sm">
          <h2 className="text-sm font-bold text-gray-500 mb-3 uppercase tracking-wide">시간</h2>
          <div className="flex items-center gap-3">
            <input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black"
            />
            <span className="text-gray-400 text-sm">~</span>
            <input
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="flex-1 border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black"
            />
          </div>
        </section>

        {error && <p className="text-red-500 text-sm text-center">{error}</p>}

        <button
          onClick={handleStart}
          disabled={loading}
          className="w-full py-4 bg-black text-white text-base font-bold rounded-2xl hover:bg-gray-800 active:scale-95 transition disabled:opacity-50"
        >
          {loading ? '코스 생성 중…' : '코스 짜기 시작'}
        </button>
      </div>
    </div>
  );
}
