import sqlite3

def create_serial_numbers_table():
    conn = sqlite3.connect('serial_numbers.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS serial_numbers (
                serial_number TEXT PRIMARY KEY,
                is_blacklisted INTEGER DEFAULT 0,
                expiration_date TEXT,
                is_active INTEGER DEFAULT 0,
                device_id TEXT,
                renewal_count INTEGER DEFAULT 0,
                last_renewal_date TEXT
            )
        ''')
        conn.commit()
        print("serial_numbers 테이블이 성공적으로 생성되었습니다.")
    except sqlite3.Error as e:
        print(f"테이블 생성 중 에러 발생: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_serial_numbers_table()