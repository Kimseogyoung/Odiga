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
          background:#000;color:#fff;
          display:flex;align-items:center;justify-content:center;
          font-size:13px;font-weight:700;
          border:2px solid #fff;
          box-shadow:0 2px 6px rgba(0,0,0,0.35);
          cursor:default;
        ">${i + 1}</div>`;

        new window.kakao.maps.CustomOverlay({ position, content, yAnchor: 1, map });
      });

      map.setBounds(bounds);
    }).catch(() => {
      console.error('[KakaoMap] SDK 로드 실패');
    });
  }, [items]);

  return <div ref={containerRef} className="w-full h-60 rounded-2xl overflow-hidden bg-gray-100" />;
}

function TimelineItem({ item, isLast }: { item: CourseItem; isLast: boolean }) {
  return (
    <div className="flex gap-4">
      {/* 타임라인 세로선 */}
      <div className="flex flex-col items-center">
        <div className="w-10 h-10 rounded-full bg-black text-white flex items-center justify-center text-lg shrink-0">
          {CATEGORY_EMOJI[item.place.category_id] ?? CATEGORY_EMOJI_FALLBACK}
        </div>
        {!isLast && <div className="w-0.5 flex-1 bg-gray-200 my-1" />}
      </div>
      {/* 내용 */}
      <div className="flex-1 pb-6">
        <div className="flex items-baseline gap-2">
          <span className="text-sm font-bold text-gray-900">{item.scheduled_time}</span>
          <span className="text-xs text-gray-400">
            {CATEGORY_LABEL[item.place.category_id]} · {item.stay_minutes}분
          </span>
        </div>
        <div className="mt-1 bg-white rounded-xl overflow-hidden shadow-sm border border-gray-100">
          <div className="flex">
            <div className="flex-1 p-4 min-w-0">
              <h3 className="font-bold text-gray-900">{item.place.name}</h3>
              <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{item.place.address}</p>
              {item.place.summary && (
                <p className="text-sm text-gray-700 mt-2 line-clamp-2">{item.place.summary}</p>
              )}
              {item.place.kakao_url && (
                <a
                  href={item.place.kakao_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-2 inline-block text-xs text-blue-500 hover:underline"
                >
                  카카오맵에서 보기
                </a>
              )}
            </div>
            {item.place.photo_url && (
              <img
                src={item.place.photo_url}
                alt={item.place.name}
                className="w-24 object-cover shrink-0"
              />
            )}
          </div>
        </div>
        {!isLast && (
          <p className="text-xs text-gray-400 mt-2 pl-1">
            도보 이동 약 {item.travel_time_to_next_minutes}분
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

  useEffect(() => {
    if (!shareToken) return;
    getCourse(shareToken)
      .then(setCourse)
      .catch(() => setError('코스를 찾을 수 없습니다.'));
  }, [shareToken]);

  function handleCopy() {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4">
        <p className="text-gray-500">{error}</p>
        <Link to="/" className="text-sm text-blue-500 hover:underline">
          처음으로 돌아가기
        </Link>
      </div>
    );
  }

  if (!course) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-400">불러오는 중…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-8 px-4">
      <div className="w-full max-w-md flex flex-col gap-5">
        {/* 헤더 */}
        <div className="text-center">
          <h1 className="text-2xl font-black text-gray-900">오늘의 코스</h1>
          <p className="text-sm text-gray-500 mt-1">
            {course.start_time} ~ {course.end_time} · {course.items.length}곳
          </p>
        </div>

        {/* 공유 */}
        <button
          onClick={handleCopy}
          className="w-full py-3 border-2 border-black text-black text-sm font-bold rounded-2xl hover:bg-black hover:text-white transition"
        >
          {copied ? '링크 복사됨!' : '공유 링크 복사'}
        </button>

        {/* 지도 */}
        <KakaoMap items={course.items} />

        {/* 시간표 */}
        <div className="pt-2">
          {course.items.map((item, i) => (
            <TimelineItem
              key={item.place.kakao_place_id}
              item={item}
              isLast={i === course.items.length - 1}
            />
          ))}
        </div>

        <Link
          to="/"
          className="text-center text-sm text-gray-400 hover:text-gray-700 pb-4"
        >
          새 코스 만들기
        </Link>
      </div>
    </div>
  );
}
