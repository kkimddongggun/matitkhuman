import http.server
import socketserver
import urllib.parse
import json
import re
import requests
import os

PORT = int(os.environ.get("PORT", 80))

class MatitkhumanHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)

        # 웹페이지에서 '/api/parse?url=네이버링크'로 요청을 보낼 때 처리
        if parsed_path.path == '/api/parse':
            query_params = urllib.parse.parse_qs(parsed_path.query)
            target_url = query_params.get('url', [''])[0]

            result = self.extract_naver_place_info(target_url)

            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        else:
            super().do_GET()

    def extract_naver_place_info(self, url):
        if not url:
            return {"success": False, "message": "링크를 입력해 주세요."}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://map.naver.com/"
        }

        try:
            # 1. 단축 링크(naver.me) 또는 전달받은 URL 리다이렉션 추적
            res = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            final_url = res.url

            match = re.search(r'(?:place|restaurant|cafe)/(\d+)', final_url)
            if not match:
                match = re.search(r'placeId[=:](\d+)', final_url)

            if not match:
                return {
                    "success": False,
                    "message": "네이버 지도 장소 링크가 아닌 것 같습니다. 가게 상세 페이지의 공유 링크를 넣어주세요."
                }

            place_id = match.group(1)

            # 2. 네이버 플레이스 공식 Summary API 호출 (429 차단 우회 및 정확한 좌표 제공)
            api_url = f"https://map.naver.com/p/api/place/summary/{place_id}"
            api_res = requests.get(api_url, headers=headers, timeout=10)

            if api_res.status_code == 200:
                data = api_res.json()
                detail = data.get("data", {}).get("placeDetail", {})

                name = detail.get("name", "").strip()

                addr_info = detail.get("address", {})
                road_addr = addr_info.get("roadAddress", "").strip()
                jibun_addr = addr_info.get("address", "").strip()
                address = road_addr or jibun_addr

                category_raw = detail.get("category", {}).get("category", "")

                coord = detail.get("coordinate", {})
                lat = coord.get("latitude")
                lng = coord.get("longitude")

                # 대표 사진 이미지 추출
                img_list = detail.get("images", {}).get("images", [])
                image_url = ""
                if img_list and isinstance(img_list, list):
                    first_img = img_list[0]
                    image_url = first_img.get("origin") or first_img.get("originalUrl") or ""

                # 음식 종류 카테고리 자동 판별
                category = "기타"
                if any(k in category_raw for k in ["한식", "찌개", "국밥", "고기", "삼겹살", "갈비", "냉면", "백반", "구이"]):
                    category = "한식"
                elif any(k in category_raw for k in ["일식", "초밥", "라멘", "돈가스", "돈카츠", "우동", "덮밥", "소바", "이자카야"]):
                    category = "일식"
                elif any(k in category_raw for k in ["중식", "짜장", "짬뽕", "마라탕", "양꼬치", "딤섬"]):
                    category = "중식"
                elif any(k in category_raw for k in ["양식", "이탈리안", "파스타", "피자", "스테이크", "버거"]):
                    category = "양식"
                elif any(k in category_raw for k in ["카페", "디저트", "베이커리", "커피", "와플", "빙수", "도넛"]):
                    category = "카페/디저트"
                elif any(k in category_raw for k in ["술집", "주점", "호프", "포차", "맥주", "와인", "펍", "바"]):
                    category = "주점/술집"
                elif any(k in category_raw for k in ["분식", "떡볶이", "김밥", "패스트푸드", "치킨"]):
                    category = "패스트푸드"

                return {
                    "success": True,
                    "name": name,
                    "address": address,
                    "category": category,
                    "category_raw": category_raw,
                    "lat": float(lat) if lat else None,
                    "lng": float(lng) if lng else None,
                    "image_url": image_url,
                    "final_url": final_url
                }
            else:
                return {"success": False, "message": f"가게 정보를 불러오지 못했습니다 (오류 코드: {api_res.status_code})"}

        except Exception as e:
            return {"success": False, "message": f"링크 분석 중 오류 발생: {str(e)}"}

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), MatitkhumanHandler) as httpd:
        print(f"맛있쿠만 서버 실행 중: http://localhost:{PORT}")
        httpd.serve_forever()
