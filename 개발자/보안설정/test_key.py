from cryptography.fernet import Fernet # type: ignore

# secret.key 파일에서 키를 읽어옵니다.
with open('secret.key', 'rb') as key_file:
    key = key_file.read()

try:
    cipher = Fernet(key)
    print("유효한 Fernet 키입니다.")
except ValueError as e:
    print(f"유효하지 않은 키입니다: {e}")