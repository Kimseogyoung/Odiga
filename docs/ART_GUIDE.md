# Odiga — 아트 가이드 (ART_GUIDE)

> 확정된 비주얼 디자인 기준 문서. 구현 시 판단 기준으로 사용.

## 목업 파일

| 화면 | 파일 | 상태 |
|------|------|------|
| 01 홈 | [mockups/01_home.html](mockups/01_home.html) | ✅ 확정 |
| 02 플래너 | [mockups/02_planner.html](mockups/02_planner.html) | ✅ 확정 |
| 03 코스 | [mockups/03_course.html](mockups/03_course.html) | ✅ 확정 |
| 비교 히스토리 (C1/C2/C3) | [mockups/compare_C1C2C3.html](mockups/compare_C1C2C3.html) | 📁 참고용 |
| 비교 히스토리 (플래너 A/B) | [mockups/02_planner_ab.html](mockups/02_planner_ab.html) | 📁 참고용 |
| 비교 히스토리 (코스 A/B) | [mockups/03_course_ab.html](mockups/03_course_ab.html) | 📁 참고용 |

---

## 1. 디자인 컨셉

> **"동글동글, 따뜻하게 — 앱이 말을 건다"**
> 투박한 흑백에서 벗어나 부드럽고 친근한 서울 여행 친구.
> 앱이 직접 대화하듯 말을 거는 대화형 UI 톤.

- 선택 기준: C1(손그림 스티커) / **C2(앱이 말을 건다)** / C3(동글 팝) 비교 후 C2 확정
- 플래닝 방식: A(집중형 1장) / **B(리스트형)** 비교 후 B 확정
- 코스 보기: A(인라인 스크롤) / **B(탭 전환)** 비교 후 B 확정

---

## 2. 레퍼런스 분석 요약

| 사이트 | 핵심 참고 포인트 |
|--------|----------------|
| wemeetplace.com | 따뜻한 포인트 색, 넉넉한 padding, 이모지 혼합 |
| modooshuttle.com | 큰 여백, 카드 위계, CTA 크고 둥글게 |
| saju-kid.com | 카드 배경 컬러 틴트, 동글 chip, 구어체 카피 |
| colormytree.me | 크림/아이보리 배경, warm tone, rounded-3xl+ |
| banggooso.com | 캐릭터/브랜드 친근감, 대화체 UI, 감성 기반 구성 |

**공통 트렌드**: `rounded-full` pill 버튼, 순검정 대신 warm 포인트 색, 크림 배경, 이모지 혼합

---

## 3. 색상 팔레트

```
--brand:       #FFD663   웜 옐로우-골드   버튼, 선택 chip, 진행 바, 타임라인 도트
--brand-light: #FFFBEA   연한 크림 옐로   진행 카드 배경, 이미지 fallback, 섹션 틴트
--brand-dark:  #B8860B   다크 골드        brand 배경 위 텍스트, 보조 라벨
--bg:          #FAFAF8   크림 아이보리    전체 페이지 배경
--card:        #FFFFFF   카드 배경
--text:        #1A1A1A   소프트 블랙      기본 텍스트
--sub:         #888888   보조 텍스트
--weak:        #BBBBBB   약한 텍스트, placeholder
--border:      #F0F0F0   경계선
```

> ✅ **확정 Pattern A** — `#FFD663` fill + `#1A1A1A` 텍스트 (WCAG 대비비 7.4:1, AAA 통과)
> `#FFD663` 위에 흰 글자는 대비 부족 — 절대 사용 금지

---

## 4. 타이포그래피

```
폰트: Pretendard Variable
CDN:  cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css

크기 체계
  11px  — 배지, 보조 라벨, 타임라인 메타
  12px  — 주소, 캡션, 카드 보조
  13px  — 본문, 리뷰, chip 텍스트
  14px  — 카드 장소명, 버튼
  15px  — 상단 바 제목
  17px  — 시간 인풋, 큰 장소명
  18px  — 로고(코스·플래너)
  22px  — 히어로 인사말, 앱 타이틀(홈)

굵기: 700(bold) / 800 위주, 900(black)은 앱 타이틀·히어로에만
```

---

## 5. Border Radius

```
카드 (place-card, timeline-card)   18–20px
진행 카드, 히어로 내부 요소         14–16px
Chip / 태그 / 버튼                 100px (rounded-full)
이미지 fallback                    카드와 동일 (overflow: hidden)
원형 아이콘 버튼 (back, close 등)  50%
타임라인 도트                      50%
드로어                             없음 (full-height panel)
```

---

## 6. 그림자

```
카드 기본    box-shadow: 0 2px 12px rgba(0,0,0,0.05), 0 0 0 1px rgba(0,0,0,0.04)
장소 카드    box-shadow: 0 2px 14px rgba(0,0,0,0.07), 0 0 0 1px rgba(0,0,0,0.04)
CTA 버튼     box-shadow: 0 8px 24px rgba(255,214,99,0.55)
Pick 버튼    box-shadow: 0 4px 14px rgba(255,214,99,0.5)
타임라인 도트 box-shadow: 0 3px 10px rgba(255,214,99,0.5)
드로어 패널  box-shadow: -8px 0 32px rgba(0,0,0,0.12)
```

---

## 7. 버튼 스타일

```
Primary CTA     bg: #FFD663  color: #1A1A1A  border-radius: 100px  font-weight: 900
                box-shadow: 0 8px 24px rgba(255,214,99,0.55)

Pick 버튼       bg: #FFD663  color: #1A1A1A  border-radius: 100px  font-size: 12–14px
                box-shadow: 0 2–4px 8–14px rgba(255,214,99,0.4–0.5)

Secondary       bg: #FFFFFF  border: 1.5px solid #F0F0F0  color: #888  border-radius: 100px
                box-shadow: 0 2px 8px rgba(0,0,0,0.04)

Chip 비선택     bg: #F4F4F0  color: #888  border-radius: 100px
Chip 선택됨     bg: #FFD663  color: #1A1A1A  border-radius: 100px  box-shadow: 0 2px 8px rgba(255,214,99,0.4)

원형 아이콘     bg: #F4F4F0 또는 rgba(0,0,0,0.1)  border-radius: 50%  border: none
```

---

## 8. 화면별 확정 패턴

### 홈 (01_home.html)

**레이아웃**: 단일 스크롤, `max-width: 480px` 중앙 정렬, 인라인 CTA (fixed 없음)

**헤더 (Hero)**
- 풀블리드 `background: #FFD663`, `padding: 16px 24px 28px`
- 좌: 유기적 손그림 말풍선 SVG 로고 (viewBox `0 0 110 85`, `stroke-width: 5.5`, fill white, stroke #1A1A1A) + "오디가" 텍스트
- 우: 햄버거 메뉴 버튼 (세 줄, 원형, `rgba(0,0,0,0.1)` 배경)
- 인사말: `font-size: 22px, font-weight: 900`
- 날씨 서브: `font-size: 13px, color: rgba(26,26,26,0.6)`

**네비게이션**: 우측 슬라이드인 드로어
- 오버레이 `rgba(0,0,0,0.4)` + 드로어 패널 280px 우측 슬라이드
- 드로어 로고: 말풍선 SVG (fill `#FFD663`) + "오디가"
- 메뉴: 홈(활성) / 내 코스 / 탐색 / 설정 / 로그인·마이페이지
- 활성 항목: `background: #FFFBEA, color: #1A1A1A, font-weight: 700`
- 외부 클릭 또는 ✕ 버튼으로 닫기, 열릴 때 `body overflow: hidden`

**콘텐츠 카드 구성**
1. 지역 선택: 4개 pill 버튼, 선택 시 brand yellow
2. 무드 칩: wrap 가능, 선택 시 brand yellow
3. 시간 선택: `background: #FFFBEA, border: 1.5px solid #FFD663, border-radius: 14px`
4. 앱 힌트 말풍선: 아바타(30px 원, brand + 검정 테두리) + `border-radius: 4px 20px 20px 20px`
5. CTA 버튼: 인라인, rounded-full, brand

---

### 플래너 (02_planner.html)

**레이아웃**: 단일 스크롤, `max-width: 480px`, `padding-bottom: 40px`

**헤더**: 로고 없음 — `position: sticky` 상단 바만
- `background: #FFFFFF, border-bottom: 1px solid #F0F0F0`
- 좌: 원형 뒤로가기 버튼 (`background: #F4F4F0`)
- 중앙: 페이지 제목 (`font-size: 15px, font-weight: 800`)
- 우: 동일 크기 spacer (시각적 균형)

**진행 카드**
- `background: #FFFBEA, border-bottom: 1px solid rgba(255,214,99,0.3)`
- 진행 바: `background: rgba(255,214,99,0.25)` 위에 `background: #FFD663` fill
- 현재 단계 텍스트: `color: #B8860B, font-weight: 800`

**카테고리 칩**
- 가로 스크롤 (`overflow-x: auto, scrollbar-width: none`)
- 선택된 칩: `background: #FFD663, color: #1A1A1A`

**장소 카드 (리스트형 B — 확정)**
- `display: flex` 가로 배치: 좌측 이미지 80px + 우측 정보
- 이미지 fallback: `linear-gradient(135deg, #FFFBEA 0%, #FFF3C0 100%)`
- 배지: `background: #FFFBEA, color: #B8860B, border-radius: 100px`
- Pick 버튼: 카드 내 우측 하단 인라인, rounded-full, brand
- 카드 간 `gap: 12px`

**하단**: "다른 장소 더 보기" secondary 버튼 (rounded-full)

---

### 코스 (03_course.html)

**레이아웃**: 단일 스크롤, `max-width: 480px`, 탭 전환 구조

**헤더 (Hero)**
- 홈과 동일한 풀블리드 brand 헤더
- 좌: 원형 뒤로가기 (rgba 배경), 중앙: 소형 로고 + "오디가", 우: `···` 더보기 버튼
- 코스 제목: `font-size: 22px, font-weight: 900`

**공유 버튼**: hero 아래 `padding: 14px 20px 0`, secondary 스타일 (rounded-full, 흰 배경)

**탭 바 (확정: B형 탭 전환)**
- `position: sticky, top: 0, z-index: 100`
- `background: #FFFFFF, border-bottom: 1px solid #F0F0F0`
- 활성 탭: `color: #1A1A1A, border-bottom: 2.5px solid #FFD663`
- 비활성 탭: `color: #BBBBBB`

**지도 탭**
- 지도 플레이스홀더: `height: 220px`, 파랑 계열 gradient (카카오맵 연동 예정)
- 코스 요약 카드 리스트: 각 장소를 `display: flex` 카드로 표시
  - 좌: 36px 원형 도트 (`background: #FFD663, box-shadow: brand shadow`)
  - 우: 장소명 + 시간 정보, 도보 시간

**타임라인 탭**
- 세로 타임라인, 도트 40px 원 (`background: #FFD663`)
- 연결선: `width: 2px, background: #F0F0F0`
- 카드: `display: flex`, 우측 이미지 84px (`background: brand-light gradient`)
- 도보 이동 텍스트: `font-size: 11px, color: #BBBBBB`
- 카카오맵 링크: `color: #B8860B, font-weight: 600`

---

## 9. 폰트 적용

```html
<!-- index.html <head> -->
<link rel="preconnect" href="https://cdn.jsdelivr.net">
<link
  href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css"
  rel="stylesheet"
/>
```

```css
/* index.css */
body {
  font-family: 'Pretendard Variable', Pretendard, -apple-system, BlinkMacSystemFont, sans-serif;
}
```

---

## 10. Tailwind 설정

```ts
// tailwind.config.ts
export default {
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#FFD663',
          light:   '#FFFBEA',
          dark:    '#B8860B',
        },
      },
      fontFamily: {
        sans: ['Pretendard Variable', 'Pretendard', 'sans-serif'],
      },
    },
  },
}
```

---

## 11. 모바일 웹 레이아웃 원칙

- `max-width: 480px; margin: 0 auto` — 모바일 뷰포트 제한
- `min-height: 100svh` — svh 단위 사용 (브라우저 크롬 고려)
- `viewport-fit: cover` — 노치/세이프에어리어 대응
- **CTA 버튼**: 콘텐츠가 짧은 페이지(홈)는 인라인. 긴 스크롤 페이지는 sticky 검토
- **fixed bottom CTA 시**: `body padding-bottom`을 버튼 높이와 맞출 것 (과도한 여백 주의)
- **하단 네비게이션 바 없음** — 우측 드로어 햄버거 메뉴로 대체

---

## 12. 네비게이션 구조

```
홈         → 우측 드로어 (햄버거 버튼)
플래너      → 상단 바 ← 뒤로가기 + 페이지 제목 (로고 없음)
코스        → 상단 히어로 헤더 ← 뒤로가기 + 소형 로고 + ··· 더보기
```

- **플로우 중간 화면(플래너)**에서는 브랜드 로고 표시하지 않음 (토스/배민/Airbnb 등 관례 따름)
- **완료/결과 화면(코스)**은 공유 진입점 역할 겸하므로 로고 유지
