import sqlite3
import os

def create_serial_table():
    print("\n=== 데이터베이스 작업 시작 ===")
    
    # 현재 폴더 확인
    print(f"현재 폴더: {os.getcwd()}")
    print(f"serials.db 파일 존재 여부: {os.path.exists('serials.db')}")
    
    try:
        conn = sqlite3.connect('serials.db')
        cursor = conn.cursor()
        
        # 기존 테이블이 있는지 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='serial_numbers'")
        if cursor.fetchone():
            print("이미 serial_numbers 테이블이 존재합니다!")
        else:
            # 테이블 생성
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS serial_numbers (
                serial_number TEXT PRIMARY KEY,
                creation_date TEXT,
                expiration_date TEXT,
                user_id TEXT,
                is_active INTEGER DEFAULT 1,
                is_blacklisted INTEGER DEFAULT 0,
                renewal_count INTEGER DEFAULT 0,
                device_id TEXT,
                last_renewal_date TEXT
            )
            ''')
            conn.commit()
            print("새로운 serial_numbers 테이블을 생성했습니다!")
        
        # 테이블 정보 확인
        cursor.execute("PRAGMA table_info(serial_numbers)")
        columns = cursor.fetchall()
        print("\n테이블 구조:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
            
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        conn.close()
        print("\n=== 데이터베이스 작업 완료 ===")

def check_serial_data():
    print("\n=== 시리얼 데이터 확인 ===")
    
    try:
        conn = sqlite3.connect('serials.db')
        cursor = conn.cursor()
        
        # 전체 데이터 개수 확인
        cursor.execute("SELECT COUNT(*) FROM serial_numbers")
        count = cursor.fetchone()[0]
        print(f"\n총 시리얼 개수: {count}")
        
        # 모든 시리얼 정보 출력
        if count > 0:
            print("\n등록된 시리얼 목록:")
            cursor.execute("SELECT serial_number, creation_date, expiration_date, is_active, device_id FROM serial_numbers")
            for row in cursor.fetchall():
                print(f"\n- 시리얼: {row[0]}")
                print(f"  생성일: {row[1]}")
                print(f"  만료일: {row[2]}")
                print(f"  활성화: {'예' if row[3] else '아니오'}")
                print(f"  기기ID: {row[4]}")
        else:
            print("\n등록된 시리얼이 없습니다!")
            
    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        conn.close()
        print("\n=== 데이터 확인 완료 ===")

if __name__ == "__main__":
    create_serial_table()
    check_serial_data()
