import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
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
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    getConstants().then(setConstants).catch(() => setError('서버에 연결할 수 없습니다.'));
  }, []);

  useEffect(() => {
    document.body.style.overflow = drawerOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [drawerOpen]);

  function toggleKeyword(id: number) {
    setKeywordIds((prev) =>
      prev.includes(id) ? prev.filter((k) => k !== id) : [...prev, id],
    );
  }

  async function handleStart() {
    if (keywordIds.length === 0) {
      setError('무드를 최소 1개 선택하세요.');
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

  const selectedRegionLabel = constants ? (constants.regions[regionId] ?? '') : '';

  if (!constants) {
    return (
      <div className="min-h-[100svh] flex items-center justify-center" style={{ background: '#FAFAF8' }}>
        <p style={{ color: '#BBBBBB' }}>{error || '로딩 중…'}</p>
      </div>
    );
  }

  return (
    <div
      className="min-h-[100svh] max-w-[480px] mx-auto"
      style={{ background: '#FAFAF8', color: '#1A1A1A' }}
    >
      {/* 히어로 */}
      <div style={{ background: '#FFD663', padding: '16px 24px 28px' }}>
        <div className="flex items-center justify-between" style={{ marginBottom: '16px' }}>
          <div className="flex items-center gap-2">
            <svg width="40" height="31" viewBox="0 0 110 85" fill="none">
              <path
                d="M28 14C42 9 58 7 72 8C86 9 98 13 104 20C110 27 110 38 108 50C106 62 100 72 90 76C78 80 58 82 44 80C38 88 34 96 32 102C30 94 28 86 26 80C18 76 12 68 10 56C8 44 8 30 14 20C18 15 22 16 28 14Z"
                fill="white"
                stroke="#1A1A1A"
                strokeWidth="5.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span style={{ fontSize: '22px', fontWeight: 900, letterSpacing: '-1px' }}>오디가</span>
          </div>
          <button
            onClick={() => setDrawerOpen(true)}
            className="flex flex-col items-center justify-center cursor-pointer"
            style={{
              width: '36px', height: '36px', borderRadius: '50%',
              background: 'rgba(0,0,0,0.1)', border: 'none',
              gap: '4px', padding: '10px',
            }}
            aria-label="메뉴 열기"
          >
            <span style={{ display: 'block', width: '16px', height: '2px', background: '#1A1A1A', borderRadius: '2px' }} />
            <span style={{ display: 'block', width: '16px', height: '2px', background: '#1A1A1A', borderRadius: '2px' }} />
            <span style={{ display: 'block', width: '16px', height: '2px', background: '#1A1A1A', borderRadius: '2px' }} />
          </button>
        </div>
        <p style={{ fontSize: '22px', fontWeight: 900, letterSpacing: '-0.6px', lineHeight: 1.35 }}>
          오늘 <strong>{selectedRegionLabel}</strong> 어때요? 🙌
        </p>
        <p style={{ marginTop: '6px', fontSize: '13px', color: 'rgba(26,26,26,0.6)', fontWeight: 500 }}>
          ✨ 취향에 맞는 코스를 짜드릴게요
        </p>
      </div>

      {/* 본문 */}
      <div style={{ padding: '20px 20px 32px', display: 'flex', flexDirection: 'column', gap: '14px' }}>

        {/* 지역 선택 */}
        <div
          className="bg-white rounded-[20px]"
          style={{ padding: '18px 16px', boxShadow: '0 2px 12px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.04)' }}
        >
          <p style={{ fontSize: '13px', fontWeight: 700, color: '#888', marginBottom: '12px' }}>📍 어디로 갈까요?</p>
          <div className="flex" style={{ gap: '7px' }}>
            {Object.entries(constants.regions).map(([id, label]) => (
              <button
                key={id}
                onClick={() => setRegionId(Number(id))}
                className="flex-1 rounded-full cursor-pointer"
                style={{
                  padding: '11px 0',
                  fontSize: '13px', fontWeight: 700, fontFamily: 'inherit',
                  border: 'none', transition: 'all 0.15s',
                  ...(regionId === Number(id)
                    ? { background: '#FFD663', color: '#1A1A1A', boxShadow: '0 3px 10px rgba(255,214,99,0.4)' }
                    : { background: '#F4F4F0', color: '#BBBBBB' }),
                }}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* 무드 선택 */}
        <div
          className="bg-white rounded-[20px]"
          style={{ padding: '18px 16px', boxShadow: '0 2px 12px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.04)' }}
        >
          <p style={{ fontSize: '13px', fontWeight: 700, color: '#888', marginBottom: '12px' }}>🏷️ 오늘의 무드</p>
          <div className="flex flex-wrap" style={{ gap: '8px' }}>
            {Object.entries(constants.keywords).map(([id, label]) => {
              const selected = keywordIds.includes(Number(id));
              return (
                <button
                  key={id}
                  onClick={() => toggleKeyword(Number(id))}
                  className="rounded-full cursor-pointer"
                  style={{
                    padding: '8px 16px',
                    fontSize: '13px', fontWeight: 600, fontFamily: 'inherit',
                    border: 'none', transition: 'all 0.15s',
                    ...(selected
                      ? { background: '#FFD663', color: '#1A1A1A', boxShadow: '0 2px 8px rgba(255,214,99,0.4)' }
                      : { background: '#F4F4F0', color: '#888' }),
                  }}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 시간 선택 */}
        <div
          className="bg-white rounded-[20px]"
          style={{ padding: '18px 16px', boxShadow: '0 2px 12px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.04)' }}
        >
          <p style={{ fontSize: '13px', fontWeight: 700, color: '#888', marginBottom: '12px' }}>🕐 몇 시부터 몇 시까지?</p>
          <div className="flex items-center" style={{ gap: '10px' }}>
            <input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="flex-1 cursor-pointer"
              style={{
                background: '#FFFBEA', border: '1.5px solid #FFD663',
                borderRadius: '14px', padding: '13px 0',
                textAlign: 'center', fontSize: '17px', fontWeight: 900,
                fontFamily: 'inherit', color: '#1A1A1A',
              }}
            />
            <span style={{ fontSize: '14px', color: '#BBBBBB' }}>—</span>
            <input
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="flex-1 cursor-pointer"
              style={{
                background: '#FFFBEA', border: '1.5px solid #FFD663',
                borderRadius: '14px', padding: '13px 0',
                textAlign: 'center', fontSize: '17px', fontWeight: 900,
                fontFamily: 'inherit', color: '#1A1A1A',
              }}
            />
          </div>
        </div>

        {/* 힌트 말풍선 */}
        <div className="flex items-end" style={{ gap: '8px' }}>
          <div
            className="shrink-0 flex items-center justify-center"
            style={{
              width: '30px', height: '30px', borderRadius: '50%',
              background: '#FFD663', border: '2px solid #1A1A1A', fontSize: '14px',
            }}
          >
            💬
          </div>
          <div
            className="flex-1"
            style={{
              background: 'white',
              borderRadius: '4px 20px 20px 20px',
              padding: '12px 16px',
              boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
              fontSize: '13px', color: '#555', lineHeight: 1.6,
            }}
          >
            ✨ 무드 칩을 고르면 취향에 딱 맞는 장소들을 골라드려요!
          </div>
        </div>

        {error && <p className="text-red-500 text-sm text-center">{error}</p>}

        {/* CTA 버튼 */}
        <button
          onClick={handleStart}
          disabled={loading}
          className="w-full cursor-pointer disabled:opacity-50"
          style={{
            padding: '18px', borderRadius: '100px',
            background: '#FFD663', color: '#1A1A1A',
            fontSize: '16px', fontWeight: 900, fontFamily: 'inherit',
            border: 'none', letterSpacing: '-0.3px',
            boxShadow: '0 8px 24px rgba(255,214,99,0.55)',
          }}
        >
          {loading ? '코스 생성 중…' : '그럼 출발할까요? →'}
        </button>

      </div>

      {/* 드로어 오버레이 */}
      <div
        className="fixed inset-0 z-[200]"
        style={{
          background: 'rgba(0,0,0,0.4)',
          opacity: drawerOpen ? 1 : 0,
          pointerEvents: drawerOpen ? 'auto' : 'none',
          transition: 'opacity 0.25s',
        }}
        onClick={() => setDrawerOpen(false)}
      />

      {/* 드로어 패널 */}
      <div
        className="fixed top-0 right-0 h-full z-[201] flex flex-col bg-white"
        style={{
          width: '280px',
          transform: drawerOpen ? 'translateX(0)' : 'translateX(100%)',
          transition: 'transform 0.28s cubic-bezier(0.4,0,0.2,1)',
          boxShadow: '-8px 0 32px rgba(0,0,0,0.12)',
        }}
      >
        {/* 드로어 헤더 */}
        <div
          className="flex items-center justify-between"
          style={{ padding: '20px 20px 16px', borderBottom: '1px solid #F0F0F0' }}
        >
          <div className="flex items-center" style={{ gap: '8px' }}>
            <svg width="28" height="22" viewBox="0 0 110 85" fill="none">
              <path
                d="M28 14C42 9 58 7 72 8C86 9 98 13 104 20C110 27 110 38 108 50C106 62 100 72 90 76C78 80 58 82 44 80C38 88 34 96 32 102C30 94 28 86 26 80C18 76 12 68 10 56C8 44 8 30 14 20C18 15 22 16 28 14Z"
                fill="#FFD663"
                stroke="#1A1A1A"
                strokeWidth="5.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span style={{ fontSize: '18px', fontWeight: 900, letterSpacing: '-0.8px' }}>오디가</span>
          </div>
          <button
            onClick={() => setDrawerOpen(false)}
            className="flex items-center justify-center cursor-pointer"
            style={{
              width: '32px', height: '32px', borderRadius: '50%',
              background: '#F4F4F0', border: 'none',
              fontSize: '16px', color: '#888',
            }}
            aria-label="메뉴 닫기"
          >
            ✕
          </button>
        </div>

        {/* 드로어 네비 */}
        <nav className="flex-1" style={{ padding: '12px 12px', display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <Link
            to="/"
            onClick={() => setDrawerOpen(false)}
            className="flex items-center no-underline"
            style={{
              gap: '12px', padding: '13px 14px', borderRadius: '14px',
              fontSize: '15px', fontWeight: 700, color: '#1A1A1A',
              background: '#FFFBEA', transition: 'background 0.12s',
            }}
          >
            <span style={{ fontSize: '18px', width: '24px', textAlign: 'center' }}>🗺️</span> 홈
          </Link>
          <span
            className="flex items-center"
            style={{
              gap: '12px', padding: '13px 14px', borderRadius: '14px',
              fontSize: '15px', fontWeight: 600, color: '#888', cursor: 'not-allowed',
            }}
          >
            <span style={{ fontSize: '18px', width: '24px', textAlign: 'center' }}>📋</span> 내 코스
          </span>
          <span
            className="flex items-center"
            style={{
              gap: '12px', padding: '13px 14px', borderRadius: '14px',
              fontSize: '15px', fontWeight: 600, color: '#888', cursor: 'not-allowed',
            }}
          >
            <span style={{ fontSize: '18px', width: '24px', textAlign: 'center' }}>🔍</span> 탐색
          </span>
          <div style={{ height: '1px', background: '#F0F0F0', margin: '8px 14px' }} />
          <span
            className="flex items-center"
            style={{
              gap: '12px', padding: '13px 14px', borderRadius: '14px',
              fontSize: '15px', fontWeight: 600, color: '#888', cursor: 'not-allowed',
            }}
          >
            <span style={{ fontSize: '18px', width: '24px', textAlign: 'center' }}>⚙️</span> 설정
          </span>
        </nav>

        {/* 드로어 푸터 */}
        <div style={{ padding: '12px 12px 28px', borderTop: '1px solid #F0F0F0' }}>
          <span
            className="flex items-center"
            style={{
              gap: '12px', padding: '13px 14px', borderRadius: '14px',
              fontSize: '15px', fontWeight: 600, color: '#888', cursor: 'not-allowed',
            }}
          >
            <span style={{ fontSize: '18px', width: '24px', textAlign: 'center' }}>👤</span> 로그인 / 마이페이지
          </span>
        </div>
      </div>
    </div>
  );
}
