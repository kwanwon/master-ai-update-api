import sqlite3

def check_table_schema():
    conn = sqlite3.connect('serial_numbers.db')
    cursor = conn.cursor()
    try:
        cursor.execute("PRAGMA table_info(serial_numbers)")
        columns = cursor.fetchall()
        if columns:
            print("현재 serial_numbers 테이블의 스키마:")
            for column in columns:
                print(column)
        else:
            print("serial_numbers 테이블이 존재하지 않습니다.")
    except sqlite3.OperationalError as e:
        print(f"에러 발생: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_table_schema()