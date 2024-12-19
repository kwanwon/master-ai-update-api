# serial_validator.py

import sqlite3
import os
from datetime import datetime, timedelta

# 데이터베이스 경로 설정
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                      '서버', '데이터베이스', 'DB관리', 'serials.db')

def get_db_connection():
    """데이터베이스 연결을 생성하고 반환합니다."""
    return sqlite3.connect(DB_PATH)

def get_device_id():
    """현재 디바이스의 고유 ID를 반환합니다."""
    import uuid
    return str(uuid.getnode())

def validate_serial_number(serial_number):
    """시리얼 넘버의 유효성을 검증하고, 디바이스와 연동합니다."""
    device_id = get_device_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT is_blacklisted, expiration_date, is_active, device_id 
            FROM serial_numbers
            WHERE serial_number = ?
        ''', (serial_number,))
        result = cursor.fetchone()

        if not result:
            return False, "잘못된 시리얼 넘버입니다."

        is_blacklisted, expiration_date_str, is_active, stored_device_id = result
        current_date = datetime.now().date()
        expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()

        if is_blacklisted:
            return False, "해당 시리얼 넘버는 블랙리스트에 등록되어 있습니다."
        elif current_date > expiration_date:
            return False, f"해당 시리얼 넘버의 유효 기간이 만료되었습니다 (만료일: {expiration_date})."
        elif is_active:
            if stored_device_id == device_id:
                return True, f"시리얼 넘버가 확인되었습니다. 만료일: {expiration_date}."
            else:
                return False, "해당 시리얼 넘버는 다른 디바이스에서 사용 중입니다."
        else:
            cursor.execute('''
                UPDATE serial_numbers
                SET is_active = 1, device_id = ?
                WHERE serial_number = ?
            ''', (device_id, serial_number))
            conn.commit()
            return True, f"시리얼 넘버가 확인되었습니다. 만료일: {expiration_date}."
    finally:
        conn.close()

def check_renewal_needed(serial_number):
    """시리얼 넘버의 만료일이 임박했는지 확인합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT expiration_date FROM serial_numbers
        WHERE serial_number = ?
    ''', (serial_number,))
    result = cursor.fetchone()

    if not result:
        return False, "시리얼 넘버를 찾을 수 없습니다."

    expiration_date_str = result[0]
    expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
    current_date = datetime.now().date()
    days_left = (expiration_date - current_date).days

    threshold_days = 3  # 임박한 갱신 기준일 수
    if 0 < days_left <= threshold_days:
        return True, f"시리얼 넘버의 만료가 {days_left}일 남았습니다. 갱신을 고려해 주세요."
    else:
        return False, ""

def renew_serial_number(serial_number):
    """시리얼 넘버를 갱신합니다."""
    device_id = get_device_id()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 시리얼 넘버 정보 가져오기
    cursor.execute('''
        SELECT expiration_date, device_id FROM serial_numbers
        WHERE serial_number = ?
    ''', (serial_number,))
    result = cursor.fetchone()

    if not result:
        return False, "시리얼 넘버를 찾을 수 없습니다."

    expiration_date_str, stored_device_id = result
    expiration_date = datetime.strptime(expiration_date_str, '%Y-%m-%d').date()
    current_date = datetime.now().date()

    if stored_device_id != device_id:
        return False, "해당 시리얼 넘버는 다른 디바이스에서 사용 중입니다. 갱신이 불가능합니다."

    # 유효 기간 연장
    new_expiration_date = expiration_date + timedelta(days=30)  # 갱신 시 30일 연장 (필요에 따라 수정 가능)

    # 시리얼 넘버 업데이트
    cursor.execute('''
        UPDATE serial_numbers
        SET expiration_date = ?, renewal_count = renewal_count + 1, last_renewal_date = ?
        WHERE serial_number = ?
    ''', (new_expiration_date.strftime('%Y-%m-%d'), current_date.strftime('%Y-%m-%d'), serial_number))
    conn.commit()
    return True, f"시리얼 넘버가 성공적으로 갱신되었습니다.\n새 만료일: {new_expiration_date}."