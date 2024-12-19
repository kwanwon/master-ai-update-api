import sqlite3
import os

def check_db_file(db_path):
    print(f"\n=== 확인 중: {db_path} ===")
    try:
        print(f"파일 크기: {os.path.getsize(db_path)} bytes")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 테이블 목록 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"테이블 목록: {tables}")
        
        if tables:  # 테이블이 있으면
            cursor.execute("SELECT * FROM serial_numbers")
            rows = cursor.fetchall()
            print(f"\n데이터 개수: {len(rows)}")
            for row in rows:
                print(f"시리얼 정보: {row}")
        
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

print("\n=== 현재 위치 ===")
print(f"현재 폴더: {os.getcwd()}")

# 현재 폴더의 serials.db 확인
print("\n=== 시리얼관리 폴더의 DB ===")
if os.path.exists("serials.db"):
    check_db_file("serials.db")
else:
    print("파일 없음: serials.db")

# 서버 폴더의 serials.db 확인
server_db = "../../서버/데이터베이스/DB관리/serials.db"
print(f"\n=== 서버 폴더의 DB ===")
if os.path.exists(server_db):
    check_db_file(server_db)
else:
    print(f"파일 없음: {server_db}")
