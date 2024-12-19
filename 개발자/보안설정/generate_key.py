from cryptography.fernet import Fernet # type: ignore

# 새로운 키 생성
key = Fernet.generate_key()

# 키를 파일에 저장
with open('secret.key', 'wb') as key_file:
    key_file.write(key)

print("새로운 secret.key 파일이 생성되었습니다.")