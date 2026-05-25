interface KakaoLatLng {}

interface KakaoLatLngBounds {
  extend(latlng: KakaoLatLng): void;
}

interface KakaoMapInstance {
  setBounds(bounds: KakaoLatLngBounds): void;
}

interface KakaoMaps {
  load(callback: () => void): void;
  LatLng: new (lat: number, lng: number) => KakaoLatLng;
  LatLngBounds: new () => KakaoLatLngBounds;
  Map: new (
    container: HTMLElement,
    options: { center: KakaoLatLng; level: number },
  ) => KakaoMapInstance;
  CustomOverlay: new (options: {
    position: KakaoLatLng;
    content: string | HTMLElement;
    yAnchor?: number;
    map: KakaoMapInstance;
  }) => void;
}

declare global {
  interface Window {
    kakao: { maps: KakaoMaps };
  }
  const kakao: { maps: KakaoMaps };
}

export {};
