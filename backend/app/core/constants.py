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
KAKAO_CATEGORY_MAP: dict[str, int] = {
    "음식점": PlaceCategory.RESTAURANT,
    "카페": PlaceCategory.CAFE,
    "디저트": PlaceCategory.CAFE,
    "제과,베이커리": PlaceCategory.CAFE,
    "쇼핑": PlaceCategory.SHOPPING,
    "의류": PlaceCategory.SHOPPING,
    "술집": PlaceCategory.BAR,
    "호프": PlaceCategory.BAR,
    "바": PlaceCategory.BAR,
    "문화시설": PlaceCategory.CULTURE,
    "전시": PlaceCategory.CULTURE,
    "갤러리": PlaceCategory.CULTURE,
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
