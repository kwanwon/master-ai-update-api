# cleanup_serials.py 파일 생성
import sqlite3
import os

# 데이터베이스 경로 설정 (이 부분이 중요해요!)
DB_PATH = os.path.join(os.path.dirname(__file__), 'serials.db')

def check_all_serials():
    """모든 시리얼 넘버 확인"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT serial_number, user_id, creation_date, expiration_date FROM serial_numbers')
    serials = cursor.fetchall()
    conn.close()
    
    print("\n=== 모든 시리얼 넘버 ===")
    for serial in serials:
        print(f"시리얼: {serial[0]}")
        print(f"사용자: {serial[1]}")
        print(f"생성일: {serial[2]}")
        print(f"만료일: {serial[3]}")
        print("-" * 50)

def delete_serial(serial_number):
    """시리얼 넘버 삭제"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM serial_numbers WHERE serial_number = ?', (serial_number,))
        conn.commit()
        print(f"시리얼 {serial_number} 삭제 완료")
    except sqlite3.Error as e:
        print(f"삭제 중 오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    while True:
        print("\n1. 모든 시리얼 확인")
        print("2. 시리얼 삭제")
        print("3. 종료")
        choice = input("선택하세요 (1-3): ")
        
        if choice == "1":
            check_all_serials()
        elif choice == "2":
            serial = input("삭제할 시리얼 번호를 입력하세요: ")
            delete_serial(serial)
        elif choice == "3":
            break
