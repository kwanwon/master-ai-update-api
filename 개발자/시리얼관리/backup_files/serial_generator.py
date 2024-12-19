# serial_generator.py

import uuid
import hashlib
import datetime

def generate_serial_number(expiration_days=365):
    # 고유 식별자 생성
    unique_id = uuid.uuid4().hex[:8].upper()
    # 생성일 설정
    creation_date = datetime.datetime.now().strftime('%Y%m%d')
    # 유효기간 설정
    expiration_date = (datetime.datetime.now() + datetime.timedelta(days=expiration_days)).strftime('%Y%m%d')
    # 시리얼 넘버의 앞부분 구성
    serial_prefix = f"SN-{unique_id}-{creation_date}-{expiration_date}"
    # 검증 코드 생성 (SHA-256 해싱 후 앞의 8자리 사용)
    verification_code = hashlib.sha256(serial_prefix.encode()).hexdigest()[:8].upper()
    # 최종 시리얼 넘버
    serial_number = f"{serial_prefix}-{verification_code}"
    return serial_number

# 테스트 코드
if __name__ == "__main__":
    new_serial = generate_serial_number()
    print(f"생성된 시리얼 넘버: {new_serial}")