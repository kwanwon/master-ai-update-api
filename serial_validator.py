from tkinter import simpledialog, messagebox
import sqlite3
from datetime import datetime, timedelta
import os
import sys

# 시리얼 스토리지 임포트를 절대 경로로 변경
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
from serial_storage import SerialStorage

# 데이터베이스 경로 설정
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                      '서버', '데이터베이스', 'DB관리', 'serials.db')

def validate_serial(serial_number, root=None):
    """시리얼 넘버의 유효성을 검증"""
    storage = SerialStorage()
    
    try:
        # 저장된 시리얼 정보 확인
        saved_serial = storage.load_serial()
        if saved_serial:
            serial_number = saved_serial['serial_number']
            expiration_date = datetime.strptime(saved_serial['expiration_date'], '%Y-%m-%d').date()
            
            # 만료 여부 확인
            days_left = (expiration_date - datetime.now().date()).days
            
            if days_left < 0:
                # 만료된 경우
                messagebox.showwarning("시리얼 만료", "시리얼 넘버가 만료되었습니다. 새로운 시리얼을 입력해주세요.")
                storage.clear_serial()
                return validate_serial(None, root)
            elif days_left <= 7:
                # 만료 임박
                messagebox.showwarning("시리얼 만료 임박", f"시리얼 넘버가 {days_left}일 후 만료됩니다.")
            
            return True
            
        # 저장된 시리얼이 없는 경우
        if serial_number is None:
            serial_number = simpledialog.askstring(
                "시리얼 넘버 입력", 
                "시리얼 넘버를 입력하세요:"
            )
            if serial_number is None:  # 취소 버튼 클릭
                return False

        # DB에서 시리얼 검증
        if validate_serial_from_db(serial_number):
            # 유효한 시리얼이면 저장
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute('SELECT expiration_date FROM serial_numbers WHERE serial_number = ?', (serial_number,))
            expiration_date = cursor.fetchone()[0]
            conn.close()
            
            storage.save_serial(serial_number, expiration_date)
            return True
        else:
            messagebox.showerror("오류", "올바르지 않은 시리얼 넘버입니다.")
            return validate_serial(None, root)
            
    except Exception as e:
        print(f"시리얼 검증 중 오류: {e}")
        return False

def validate_serial_from_db(serial_number):
    """시리얼 넘버의 유효성을 검증하고, 디바이스와 연동합니다."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT expiration_date FROM serial_numbers
            WHERE serial_number = ?
        ''', (serial_number,))
        result = cursor.fetchone()

        if not result:
            return False

        # 만료일 체크
        expiration_date = datetime.strptime(result[0], '%Y-%m-%d').date()
        if expiration_date < datetime.now().date():
            return False

        return True

    finally:
        cursor.close()
        conn.close()
