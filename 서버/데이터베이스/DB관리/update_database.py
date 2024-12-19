# update_database.py

import sqlite3

def update_database():
    conn = sqlite3.connect('serial_numbers.db')
    cursor = conn.cursor()
    
    # 테이블 정보 조회
    cursor.execute("PRAGMA table_info(serial_numbers);")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'is_active' not in columns:
        cursor.execute("ALTER TABLE serial_numbers ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 0;")
        conn.commit()
        print("is_active 필드가 추가되었습니다.")
    else:
        print("is_active 필드가 이미 존재합니다.")
    
    conn.close()

if __name__ == "__main__":
    update_database()