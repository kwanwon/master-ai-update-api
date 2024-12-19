import os
import sqlite3
from datetime import datetime

def get_device_id():
    import uuid
    return str(uuid.getnode())

print("\n=== 프로그램 정보 확인 ===")
print(f"현재 시간: {datetime.now()}")
print(f"현재 기기 ID: {get_device_id()}")

print("\n=== 임시 폴더 확인 ===")
temp_paths = [
    ".",
    "./임시",
    "../임시",
    "../../임시"
]

for path in temp_paths:
    if os.path.exists(path):
        print(f"\n폴더 확인: {path}")
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.db'):
                    full_path = os.path.join(root, file)
                    print(f"\n발견된 DB: {full_path}")
                    try:
                        conn = sqlite3.connect(full_path)
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = cursor.fetchall()
                        print(f"테이블: {tables}")
                        if 'serial_numbers' in str(tables):
                            cursor.execute("SELECT * FROM serial_numbers")
                            rows = cursor.fetchall()
                            print(f"데이터 수: {len(rows)}")
                            if rows:
                                print("첫 번째 시리얼:", rows[0])
                        conn.close()
                    except Exception as e:
                        print(f"에러: {e}")
