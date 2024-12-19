import requests
import os
import json

class UpdateClient:
    def __init__(self):
        self.api_url = "http://localhost:5000"
        self.current_version = "1.0.0"  # 현재 버전
        
    def check_update(self):
        """서버에서 최신 버전 확인"""
        try:
            response = requests.get(f"{self.api_url}/check_version")
            if response.status_code == 200:
                latest = response.json()
                print("\n[최신 버전 정보]")
                print(f"현재 버전: {self.current_version}")
                print(f"최신 버전: {latest['version']}")
                print(f"업데이트 날짜: {latest['release_date']}")
                print(f"설명: {latest['description']}")
                print(f"필수 업데이트: {'예' if latest['required'] else '아니오'}")
                
                return latest
            else:
                print("버전 확인 실패:", response.json().get('error'))
                return None
                
        except Exception as e:
            print("버전 확인 중 오류:", str(e))
            return None
            
    def download_update(self, version):
        """업데이트 파일 다운로드"""
        try:
            print(f"\n[{version} 버전 다운로드 중...]")
            response = requests.get(f"{self.api_url}/download_all/{version}")
            
            if response.status_code == 200:
                # 다운로드 폴더 생성
                os.makedirs('downloads', exist_ok=True)
                
                # 파일 저장
                file_path = os.path.join('downloads', f'update_{version}.zip')
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                    
                print(f"다운로드 완료: {file_path}")
                return True
            else:
                print("다운로드 실패:", response.json().get('error'))
                return False
                
        except Exception as e:
            print("다운로드 중 오류:", str(e))
            return False 