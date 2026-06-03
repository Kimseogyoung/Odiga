import { useState, useEffect, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCourse } from '../api/courses';
import { CATEGORY_LABEL, CATEGORY_EMOJI, CATEGORY_EMOJI_FALLBACK } from '../constants';
import type { CourseResponse, CourseItem } from '../types';

const KAKAO_MAP_KEY = import.meta.env.VITE_KAKAO_MAP_KEY as string;

function loadKakaoSDK(): Promise<void> {
  return new Promise((resolve, reject) => {
    if (window.kakao?.maps) {
      window.kakao.maps.load(resolve);
      return;
    }
    const script = document.createElement('script');
    script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${KAKAO_MAP_KEY}&autoload=false`;
    script.onload = () => window.kakao.maps.load(resolve);
    script.onerror = reject;
    document.head.appendChild(script);
  });
}

function KakaoMap({ items }: { items: CourseItem[] }) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || items.length === 0) return;

    loadKakaoSDK().then(() => {
      if (!containerRef.current) return;
      const center = new window.kakao.maps.LatLng(items[0].place.lat, items[0].place.lng);
      const map = new window.kakao.maps.Map(containerRef.current, { center, level: 5 });
      const bounds = new window.kakao.maps.LatLngBounds();

      items.forEach((item, i) => {
        const position = new window.kakao.maps.LatLng(item.place.lat, item.place.lng);
        bounds.extend(position);

        const content = `<div style="
          width:28px;height:28px;border-radius:50%;
          background:#FFD663;color:#1A1A1A;
          display:flex;align-items:center;justify-content:center;
          font-size:13px;font-weight:700;
          border:2px solid #fff;
          box-shadow:0 2px 6px rgba(255,214,99,0.5);
          cursor:default;
        ">${i + 1}</div>`;

        new window.kakao.maps.CustomOverlay({ position, content, yAnchor: 1, map });
      });

      map.setBounds(bounds);
    }).catch(() => {
      console.error('[KakaoMap] SDK 로드 실패');
    });
  }, [items]);

  return <div ref={containerRef} className="w-full h-[220px]" style={{ background: '#dff0f8' }} />;
}

function TimelineItem({ item, isLast }: { item: CourseItem; isLast: boolean }) {
  return (
    <div className="flex gap-3">
      {/* 타임라인 좌측 */}
      <div className="flex flex-col items-center">
        <div
          className="w-10 h-10 rounded-full shrink-0 flex items-center justify-center text-lg"
          style={{
            background: '#FFD663',
            color: '#3D2800',
            boxShadow: '0 3px 10px rgba(255,214,99,0.5)',
          }}
        >
          {CATEGORY_EMOJI[item.place.category_id] ?? CATEGORY_EMOJI_FALLBACK}
        </div>
        {!isLast && <div className="w-0.5 flex-1 my-1" style={{ background: '#F0F0F0' }} />}
      </div>

      {/* 내용 */}
      <div className="flex-1 pb-5">
        <div className="flex items-baseline gap-1.5 mt-1.5">
          <span className="text-sm font-extrabold">{item.scheduled_time}</span>
          <span className="text-[11px]" style={{ color: '#BBBBBB' }}>
            {CATEGORY_LABEL[item.place.category_id]} · {item.stay_minutes}분
          </span>
        </div>
        <div
          className="mt-2 bg-white rounded-[18px] overflow-hidden"
          style={{ boxShadow: '0 2px 10px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.04)' }}
        >
          <div className="flex">
            <div className="flex-1 p-3.5 min-w-0">
              <h3 className="text-sm font-bold">{item.place.name}</h3>
              <p className="text-[11px] mt-[3px] truncate" style={{ color: '#BBBBBB' }}>
                {item.place.address}
              </p>
              {item.place.summary && (
                <p className="text-xs mt-1.5 line-clamp-2 leading-[1.5]" style={{ color: '#666' }}>
                  {item.place.summary}
                </p>
              )}
              {item.place.kakao_url && (
                <a
                  href={item.place.kakao_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1.5 inline-block text-[11px] font-semibold"
                  style={{ color: '#B8860B' }}
                >
                  카카오맵에서 보기 →
                </a>
              )}
            </div>
            {item.place.photo_url ? (
              <img
                src={item.place.photo_url}
                alt={item.place.name}
                className="w-[84px] object-cover shrink-0"
              />
            ) : (
              <div
                className="w-[84px] shrink-0 flex items-center justify-center text-3xl"
                style={{ background: 'linear-gradient(135deg, #FFFBEA 0%, #FFF3C0 100%)' }}
              >
                {CATEGORY_EMOJI[item.place.category_id] ?? CATEGORY_EMOJI_FALLBACK}
              </div>
            )}
          </div>
        </div>
        {!isLast && (
          <p className="text-[11px] mt-[7px]" style={{ color: '#BBBBBB' }}>
            🚶 도보 이동 약 {item.travel_time_to_next_minutes}분
          </p>
        )}
      </div>
    </div>
  );
}

export default function CoursePage() {
  const { shareToken } = useParams<{ shareToken: string }>();
  const [course, setCourse] = useState<CourseResponse | null>(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'map' | 'timeline'>('map');

  useEffect(() => {
    if (!shareToken) return;
    getCourse(shareToken)
      .then(setCourse)
      .catch(() => setError('코스를 찾을 수 없습니다.'));
  }, [shareToken]);

  function handleCopy() {
    const url = window.location.href;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url)
        .then(() => markCopied())
        .catch(() => fallbackCopy(url));
    } else {
      fallbackCopy(url);
    }
  }

  function fallbackCopy(text: string) {
    const el = document.createElement('textarea');
    el.value = text;
    el.style.cssText = 'position:fixed;top:0;left:0;opacity:0;font-size:16px;';
    el.setAttribute('readonly', '');
    document.body.appendChild(el);
    el.focus();
    el.setSelectionRange(0, 999999);
    if (document.execCommand('copy')) markCopied();
    document.body.removeChild(el);
  }

  function markCopied() {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  if (error) {
    return (
      <div className="min-h-[100svh] flex flex-col items-center justify-center gap-4">
        <p style={{ color: '#888' }}>{error}</p>
        <Link to="/" className="text-sm font-semibold" style={{ color: '#B8860B' }}>
          처음으로 돌아가기
        </Link>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="min-h-[100svh] flex items-center justify-center">
        <p style={{ color: '#BBBBBB' }}>불러오는 중…</p>
      </div>
    );
  }

  return (
    <div
      className="min-h-[100svh] max-w-[480px] mx-auto pb-10"
      style={{ background: '#FAFAF8', color: '#1A1A1A' }}
    >
      {/* 히어로 헤더 */}
      <div style={{ background: '#FFD663', padding: '16px 20px 20px' }}>
        <div className="flex items-center justify-between mb-3">
          <Link
            to="/"
            className="w-8 h-8 rounded-full flex items-center justify-center text-base"
            style={{ background: 'rgba(0,0,0,0.1)', textDecoration: 'none', color: '#1A1A1A' }}
          >
            ←
          </Link>
          <div className="flex items-center gap-1.5">
            <svg width="26" height="20" viewBox="0 0 110 85" fill="none">
              <path
                d="M28 14C42 9 58 7 72 8C86 9 98 13 104 20C110 27 110 38 108 50C106 62 100 72 90 76C78 80 58 82 44 80C38 88 34 96 32 102C30 94 28 86 26 80C18 76 12 68 10 56C8 44 8 30 14 20C18 15 22 16 28 14Z"
                fill="white"
                stroke="#1A1A1A"
                strokeWidth="5.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <span className="text-[17px] font-black tracking-tight">오디가</span>
          </div>
          <button
            className="w-8 h-8 rounded-full flex items-center justify-center text-lg cursor-pointer"
            style={{ background: 'rgba(0,0,0,0.1)', border: 'none', letterSpacing: 0 }}
          >
            ···
          </button>
        </div>
        <h1 className="text-[22px] font-black tracking-tight">오늘의 코스 🗺️</h1>
        <p className="mt-1 text-[13px] font-medium" style={{ color: 'rgba(26,26,26,0.6)' }}>
          {course.start_time} ~ {course.end_time} · {course.items.length}곳
        </p>
      </div>

      {/* 공유 버튼 */}
      <div style={{ padding: '14px 20px 0' }}>
        <button
          onClick={handleCopy}
          className="w-full flex items-center justify-center gap-1.5 rounded-full text-[13px] font-bold cursor-pointer"
          style={{
            padding: '13px',
            background: 'white',
            border: '1.5px solid #F0F0F0',
            color: '#888',
            boxShadow: '0 2px 8px rgba(0,0,0,0.04)',
          }}
        >
          {copied ? '✓ 링크 복사됨!' : '🔗 공유 링크 복사'}
        </button>
      </div>

      {/* 탭 바 */}
      <div
        className="flex sticky top-0 z-50"
        style={{ background: 'white', borderBottom: '1px solid #F0F0F0', marginTop: '14px' }}
      >
        {(['map', 'timeline'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className="flex-1 text-sm font-bold cursor-pointer"
            style={{
              padding: '14px 0',
              background: 'transparent',
              borderTop: 'none',
              borderLeft: 'none',
              borderRight: 'none',
              borderBottom: activeTab === tab ? '2.5px solid #FFD663' : '2.5px solid transparent',
              color: activeTab === tab ? '#1A1A1A' : '#BBBBBB',
              transition: 'color 0.15s',
            }}
          >
            {tab === 'map' ? '🗺️ 지도' : '📋 타임라인'}
          </button>
        ))}
      </div>

      {/* 지도 탭 — 항상 DOM에 유지 (KakaoMap 초기화 보존) */}
      <div style={{ display: activeTab === 'map' ? 'block' : 'none' }}>
        <KakaoMap items={course.items} />
        <div style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <p className="text-xs font-bold" style={{ color: '#BBBBBB', letterSpacing: '0.3px', marginBottom: '2px' }}>
            코스 요약 · {course.items.length}곳
          </p>
          {course.items.map((item, i) => (
            <div
              key={item.place.kakao_place_id}
              className="flex items-center gap-3 bg-white rounded-[16px]"
              style={{
                padding: '12px 14px',
                boxShadow: '0 1px 6px rgba(0,0,0,0.04), 0 0 0 1px rgba(0,0,0,0.04)',
              }}
            >
              <div
                className="w-9 h-9 rounded-full shrink-0 flex items-center justify-center text-base"
                style={{ background: '#FFD663', boxShadow: '0 2px 8px rgba(255,214,99,0.4)' }}
              >
                {CATEGORY_EMOJI[item.place.category_id] ?? CATEGORY_EMOJI_FALLBACK}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-bold truncate">{item.place.name}</p>
                <p className="text-xs mt-0.5" style={{ color: '#888' }}>
                  {item.scheduled_time} · {CATEGORY_LABEL[item.place.category_id]} · {item.stay_minutes}분
                </p>
              </div>
              <span className="text-[11px] shrink-0" style={{ color: '#BBBBBB' }}>
                {i === 0
                  ? '🚶 출발'
                  : `🚶 ${course.items[i - 1].travel_time_to_next_minutes ?? '?'}분`}
              </span>
            </div>
          ))}
          <Link to="/" className="block text-center text-[13px]" style={{ color: '#BBBBBB', padding: '16px 0 4px', textDecoration: 'none' }}>
            + 새 코스 만들기
          </Link>
        </div>
      </div>

      {/* 타임라인 탭 */}
      <div style={{ display: activeTab === 'timeline' ? 'block' : 'none' }}>
        <div style={{ padding: '16px 20px' }}>
          {course.items.map((item, i) => (
            <TimelineItem
              key={item.place.kakao_place_id}
              item={item}
              isLast={i === course.items.length - 1}
            />
          ))}
          <Link to="/" className="block text-center text-[13px]" style={{ color: '#BBBBBB', padding: '16px 0 4px', textDecoration: 'none' }}>
            + 새 코스 만들기
          </Link>
        </div>
      </div>
    </div>
  );
}
