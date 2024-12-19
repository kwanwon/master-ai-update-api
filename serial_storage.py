import json
import os
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