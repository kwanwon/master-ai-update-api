import requests
import os
import json
import sys
import shutil
import subprocess
from version import VERSION
from datetime import datetime, timedelta

class SerialStorage:
    def __init__(self):
        self.storage_path = os.path.join(os.path.expanduser('~'), '.ai사범님', 'serial.json')
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
    
    def save_serial(self, serial_number, expiration_date):
        """시리얼 정보를 저장"""
        data = {
            'serial_number': serial_number,
            'expiration_date': expiration_date
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f)
    
    def load_serial(self):
        """저장된 시리얼 정보를 로드"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None
    
    def clear_serial(self):
        """저장된 시리얼 정보를 삭제"""
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)

def check_for_updates():
    """새로운 버전이 있는지 확인하는 함수"""
    try:
        # 업데이트 상태 파일 확인
        update_flag_file = os.path.join(os.path.dirname(__file__), '.update_completed')
        if os.path.exists(update_flag_file):
            return False
            
        # 서버에서 최신 버전 정보를 가져오는 로직 (현재는 하드코딩)
        latest_version = "1.1.0"
        current_version = VERSION
        
        print(f"현재 버전: {current_version}")
        print(f"최신 버전: {latest_version}")
        
        # 버전 비교
        return latest_version > current_version
        
    except Exception as e:
        print(f"업데이트 확인 중 오류 발생: {e}")
        return False

def perform_update():
    """업데이트를 수행하는 함수"""
    try:
        print("업데이트를 시작합니다...")
        
        # 1. 현재 디렉토리 확인
        current_dir = os.path.dirname(os.path.abspath(__file__))
        backup_dir = os.path.join(current_dir, "backup")
        update_dir = os.path.join(current_dir, "update")
        
        # 2. 백업 디렉토리 생성
        os.makedirs(backup_dir, exist_ok=True)
        os.makedirs(update_dir, exist_ok=True)
        
        # 3. 현재 파일들 백업
        print("프로그램 백업 중...")
        for file in os.listdir(current_dir):
            if file.endswith('.py'):
                shutil.copy2(
                    os.path.join(current_dir, file),
                    os.path.join(backup_dir, file)
                )
        
        # 4. 버전 정보 업데이트
        version_file = os.path.join(current_dir, 'version.py')
        with open(version_file, 'w') as f:
            f.write(f'VERSION = "1.1.0"')  # 새 버전으로 업데이트
        
        print("업데이트가 완료되었습니다.")
        return True
        
    except Exception as e:
        print(f"업데이트 중 오류: {e}")
        return False 