import json
import os
from datetime import datetime

class SerialStorage:
    def __init__(self):
        """시리얼 저장소 초기화"""
        self.storage_dir = os.path.dirname(os.path.abspath(__file__))
        self.storage_file = os.path.join(self.storage_dir, 'serial_info.json')

    def save_serial(self, serial_number, expiration_date):
        """
        시리얼 정보를 저장
        
        Args:
            serial_number (str): 시리얼 번호
            expiration_date (str): 만료일 (YYYY-MM-DD 형식)
        """
        data = {
            'serial_number': serial_number,
            'expiration_date': expiration_date,
            'saved_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"시리얼 저장 중 오류: {e}")
            return False

    def load_serial(self):
        """
        저장된 시리얼 정보를 로드
        
        Returns:
            dict: 시리얼 정보 또는 None
        """
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"시리얼 로드 중 오류: {e}")
        return None

    def clear_serial(self):
        """저장된 시리얼 정보를 삭제"""
        try:
            if os.path.exists(self.storage_file):
                os.remove(self.storage_file)
            return True
        except Exception as e:
            print(f"시리얼 삭제 중 오류: {e}")
            return False

    def is_serial_valid(self):
        """
        저장된 시리얼이 유효한지 확인
        
        Returns:
            bool: 유효하면 True, 아니면 False
        """
        serial_info = self.load_serial()
        if not serial_info:
            return False

        try:
            expiration_date = datetime.strptime(
                serial_info['expiration_date'], 
                '%Y-%m-%d'
            ).date()
            return expiration_date >= datetime.now().date()
        except Exception as e:
            print(f"시리얼 유효성 검사 중 오류: {e}")
            return False