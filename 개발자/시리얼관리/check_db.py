# check_db.py
import sqlite3
import os

# 데이터베이스 경로 설정
DB_PATH = '/Users/gm2hapkido/Desktop/masterAI/서버/데이터베이스/DB관리/serial_numbers.db'

def check_current_folder():
    """현재 폴더 확인하기"""
    print("\n=== 현재 위치 ===")
    print(f"현재 폴더: {os.getcwd()}")
    
    print("\n=== 폴더 내 파일들 ===")
    for file in os.listdir():
        print(f"파일: {file}")

def check_database():
    """데이터베이스 확인하기"""
    print("\n=== 데이터베이스 확인 ===")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM serial_numbers")
        records = cursor.fetchall()
        print(f"총 시리얼 수: {len(records)}")
        for record in records:
            print("\n--- 시리얼 정보 ---")
            print(f"시리얼 번호: {record[0]}")
            print(f"생성일: {record[1]}")
            print(f"만료일: {record[2]}")
    except Exception as e:
        print(f"확인 중 오류 발생: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== 프로그램 시작 ===")
    check_current_folder()
    check_database()
    print("\n=== 프로그램 종료 ===")