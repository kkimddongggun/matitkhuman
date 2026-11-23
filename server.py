import http.server
import socketserver
import urllib.parse
import json
import re
import requests

PORT = 80

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
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        else:
            # 그 외 일반 접속(http://localhost)은 기존처럼 index.html을 보여줌
            super().do_GET()

    def extract_naver_place_info(self, url):
        if not url:
            return {"success": False, "message": "링크를 입력해 주세요."}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            # 1. naver.me 단축 링크를 따라가 최종 URL과 장소 고유 번호(ID) 추출
            res = requests.get(url, headers=headers, allow_redirects=True, timeout=5)
            final_url = res.url

            match = re.search(r'(?:place|restaurant|cafe)/(\d+)', final_url)
            if not match:
                return {"success": False, "message": "네이버 지도 장소 링크가 아닌 것 같습니다. 가게 상세 페이지의 공유 링크를 넣어주세요."}

            place_id = match.group(1)

            # 2. 모바일 네이버 플레이스 페이지에서 가게 이름과 주소 정보 가져오기
            place_url = f"https://m.place.naver.com/place/{place_id}/home"
            place_res = requests.get(place_url, headers=headers, timeout=5)
            html = place_res.text

            # 가게 이름 추출 (og:title 메타 태그)
            title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            name = title_match.group(1) if title_match else ""
            name = re.sub(r'\s*[:|-]\s*네이버.*$', '', name).strip()

            # 요약 정보 추출 (og:description 메타 태그)
            desc_match = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            desc = desc_match.group(1).strip() if desc_match else ""

            # 도로명 주소 패턴 추출
            addr_match = re.search(
                r'((?:서울|경기|인천|부산|대구|광주|대전|울산|세종|강원|충북|충남|전북|전남|경북|경남|제주)[가-힣0-9\s\-]+?(?:로|길)\s*\d+(?:-\d+)?)',
                html
            )
            address = addr_match.group(1).strip() if addr_match else ""

            return {
                "success": True,
                "name": name,
                "address": address,
                "description": desc,
                "final_url": url
            }

        except Exception as e:
            return {"success": False, "message": f"링크 분석 중 오류 발생: {str(e)}"}

with socketserver.TCPServer(("", PORT), MatitkhumanHandler) as httpd:
    print(f"맛있쿠만 서버 실행 중: http://localhost:{PORT}")
    httpd.serve_forever()