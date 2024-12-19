import sqlite3

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
    check_serial_data()
