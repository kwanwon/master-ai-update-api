import os
import sqlite3
from datetime import datetime

def trace_files():
    print("\n=== 프로그램 파일 추적 ===")
    
    # 1. 현재 실행 중인 프로그램 확인
    print("\n1. 프로그램 파일들:")
    program_files = [f for f in os.listdir('.') if f.endswith('.py')]
    for file in program_files:
        print(f"- {file}")
        # 파일 내용에서 'serials.db' 또는 'serial_numbers' 문자열 찾기
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'serials.db' in content or 'serial_numbers' in content:
                    print(f"  → DB 관련 코드 포함")
        except Exception as e:
            print(f"  → 읽기 에러: {e}")
    
    # 2. 상위 폴더들 확인
    print("\n2. 상위 폴더 구조:")
    current = os.path.abspath('.')
    for _ in range(3):  # 3단계 상위까지만
        parent = os.path.dirname(current)
        print(f"\n확인 중: {parent}")
        try:
            items = os.listdir(parent)
            for item in items:
                full_path = os.path.join(parent, item)
                if os.path.isdir(full_path):
                    print(f"- 폴더: {item}")
                elif item.endswith('.db'):
                    print(f"- DB파일: {item}")
        except Exception as e:
            print(f"접근 에러: {e}")
        current = parent

    # 3. 실행 중인 프로세스 정보
    print("\n3. 현재 상태:")
    print(f"작업 폴더: {os.getcwd()}")
    print(f"기기 ID: {hex(hash(os.getlogin()))}")
    print(f"시간: {datetime.now()}")

if __name__ == "__main__":
    trace_files()
