from enum import IntEnum


class Region(IntEnum):
    SEONGSU = 1
    HONGDAE = 2
    YEONNAM = 3


class PlaceCategory(IntEnum):
    RESTAURANT = 1
    CAFE = 2
    SHOPPING = 3
    BAR = 4
    CULTURE = 5


class Keyword(IntEnum):
    VINTAGE = 1
    HIP = 2
    KITSCH = 3
    OTAKU = 4
    CUTE = 5
    DESSERT = 6
    VIBE = 7
    DELICIOUS = 8
    HOTPLACE = 9
    WAITING = 10
    PHOTOGENIC = 11
    QUIET = 12
    SPACIOUS = 13
    PARKING = 14
    PHOTOSPOT = 15


REGION_LABEL: dict[int, str] = {
    Region.SEONGSU: "성수",
    Region.HONGDAE: "홍대",
    Region.YEONNAM: "연남",
}

# list of (위도, 경도, 반경m)
# pageable_count 45 제한 우회를 위해 지역을 격자 분할.
# 각 원 반경 500m, 인접 원과 ~30% 중복으로 누락 최소화.
# 성수: 뚝섬역/서울숲 · 성수역 · 성수동 남쪽 3포인트
# 홍대: 홍대입구역 · 홍대 남쪽/클럽거리 2포인트
# 연남: 경의선숲길 중심 · 연남동 북쪽 2포인트
REGION_GRID: dict[int, list[tuple[float, float, int]]] = {
    Region.SEONGSU: [
        (37.5474, 127.0447, 500),  # 뚝섬역 / 서울숲 카페거리
        (37.5443, 127.0557, 500),  # 성수역 / 성수 카페거리
        (37.5400, 127.0500, 500),  # 성수동 2가 남쪽
    ],
    Region.HONGDAE: [
        (37.5577, 126.9247, 500),  # 홍대입구역
        (37.5520, 126.9210, 500),  # 홍대 남쪽 / 클럽거리
    ],
    Region.YEONNAM: [
        (37.5650, 126.9230, 500),  # 연남동 / 경의선 숲길 중심
        (37.5700, 126.9270, 500),  # 연남동 북쪽
    ],
}

PLACE_CATEGORY_LABEL: dict[int, str] = {
    PlaceCategory.RESTAURANT: "음식점",
    PlaceCategory.CAFE: "카페",
    PlaceCategory.SHOPPING: "쇼핑",
    PlaceCategory.BAR: "바/펍",
    PlaceCategory.CULTURE: "전시/문화",
}

KEYWORD_LABEL: dict[int, str] = {
    Keyword.VINTAGE: "빈티지",
    Keyword.HIP: "힙한",
    Keyword.KITSCH: "키치한",
    Keyword.OTAKU: "오타쿠",
    Keyword.CUTE: "귀여운",
    Keyword.DESSERT: "디저트",
    Keyword.VIBE: "감성",
    Keyword.DELICIOUS: "존맛",
    Keyword.HOTPLACE: "핫플",
    Keyword.WAITING: "웨이팅 맛집",
    Keyword.PHOTOGENIC: "사진찍기 좋은",
    Keyword.QUIET: "조용한",
    Keyword.SPACIOUS: "넓은",
    Keyword.PARKING: "주차장",
    Keyword.PHOTOSPOT: "포토스팟",
}

# 카테고리별 기본 체류시간 (분)
STAY_MINUTES: dict[int, int] = {
    PlaceCategory.RESTAURANT: 60,
    PlaceCategory.CAFE: 90,
    PlaceCategory.SHOPPING: 60,
    PlaceCategory.BAR: 90,
    PlaceCategory.CULTURE: 90,
}

# 카카오맵 카테고리 원본 → PlaceCategory 매핑
# 카카오는 "음식점 > 카페" 형태로 상위 카테고리를 앞에 붙임.
# "음식점"을 먼저 두면 카페·술집도 음식점으로 오분류되므로
# 구체적인 하위 카테고리를 앞에, "음식점"은 마지막에 배치.
KAKAO_CATEGORY_MAP: dict[str, int] = {
    "카페": PlaceCategory.CAFE,
    "디저트": PlaceCategory.CAFE,
    "제과,베이커리": PlaceCategory.CAFE,
    "술집": PlaceCategory.BAR,
    "호프": PlaceCategory.BAR,
    "바": PlaceCategory.BAR,
    "문화시설": PlaceCategory.CULTURE,
    "문화,예술": PlaceCategory.CULTURE,
    "전시": PlaceCategory.CULTURE,
    "갤러리": PlaceCategory.CULTURE,
    "쇼핑": PlaceCategory.SHOPPING,
    "의류": PlaceCategory.SHOPPING,
    "가정,생활": PlaceCategory.SHOPPING,
    "음식점": PlaceCategory.RESTAURANT,
}

# 서브카테고리 int ID → 한국어 라벨 (카테고리 ID * 100 + 순번)
SUBCATEGORY_LABEL: dict[int, str] = {
    101: "한식",   102: "고기",   103: "중식",   104: "양식",   105: "일식",   106: "면류",
    201: "베이커리", 202: "테마카페", 203: "커피",
    301: "의류",   302: "인테리어", 303: "소품·잡화",
    401: "호프",   402: "칵테일", 403: "이자카야", 404: "와인바", 405: "포장마차",
    501: "공연",   502: "전시",   503: "미술관",
}

# 서브카테고리 int ID → 카카오 카테고리 키워드 목록 (서브스트링 매칭)
# embed_places.py 인덱싱 + planner.py 검색 양쪽에서 참조
SUBCATEGORY_KEYWORDS: dict[int, list[str]] = {
    101: ["한식"],
    102: ["육류,고기"],
    103: ["중국요리", "양꼬치"],
    104: ["이탈리안", "피자", "햄버거", "스테이크,립", "멕시칸,브라질"],
    105: ["초밥,롤", "일본식라면", "돈까스,우동", "일식집"],
    106: ["일본식라면", "국수", "냉면", "돈까스,우동"],
    201: ["제과,베이커리"],
    202: ["테마카페"],
    203: ["커피전문점"],
    301: ["의류판매"],
    302: ["인테리어장식판매"],
    303: ["패션잡화점", "디자인문구"],
    401: ["호프,요리주점"],
    402: ["칵테일바"],
    403: ["일본식주점"],
    404: ["와인바"],
    405: ["실내포장마차"],
    501: ["공연장,연극극장"],
    502: ["전시관"],
    503: ["미술관"],
}

# 카테고리 ID → 소속 서브카테고리 int ID 목록
CATEGORY_SUBCATEGORIES: dict[int, list[int]] = {
    PlaceCategory.RESTAURANT: [101, 102, 103, 104, 105, 106],
    PlaceCategory.CAFE:       [201, 202, 203],
    PlaceCategory.SHOPPING:   [301, 302, 303],
    PlaceCategory.BAR:        [401, 402, 403, 404, 405],
    PlaceCategory.CULTURE:    [501, 502, 503],
}

# 키워드 → 카카오 검색 쿼리 접미어 목록 (복수 쿼리 → 결과 합산)
KEYWORD_SEARCH_QUERIES: dict[int, list[str]] = {
    Keyword.VINTAGE:   ["빈티지 카페", "빈티지 쇼핑"],
    Keyword.HIP:       ["힙한 카페", "힙한 맛집"],
    Keyword.KITSCH:    ["키치 카페", "키치 소품샵"],
    Keyword.OTAKU:     ["오타쿠 카페", "피규어 카페"],
    Keyword.CUTE:      ["귀여운 카페", "캐릭터 카페"],
    Keyword.DESSERT:   ["디저트 카페", "케이크 카페"],
    Keyword.VIBE:      ["감성카페", "감성 맛집"],
    Keyword.DELICIOUS: ["맛집", "유명 맛집"],
    Keyword.HOTPLACE:  ["카페", "맛집"],
    Keyword.WAITING:   ["웨이팅 맛집", "줄서는 맛집"],
    Keyword.PHOTOGENIC:["사진맛집", "포토존 카페"],
    Keyword.QUIET:     ["조용한 카페", "공부 카페"],
    Keyword.SPACIOUS:  ["넓은 카페", "대형 카페"],
    Keyword.PARKING:   ["주차 카페", "주차 맛집"],
    Keyword.PHOTOSPOT: ["포토스팟 카페", "인생사진 카페"],
}
